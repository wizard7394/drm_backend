from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from app.models.course import Course, CourseNode
from app.models.license import License
from app.models.user import User
from app.core.errors import AppErrors
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    NodeCreate,
    NodeUpdate,
    AutoBuildRequest,
)


class CourseService:
    @staticmethod
    async def get_course_details(course_id: int, current_user: User, db: AsyncSession):
        license_query = await db.execute(
            select(License).where(
                License.user_id == current_user.id,
                License.course_id == course_id,
                License.is_active,
            )
        )
        db_license = license_query.scalars().first()

        if not db_license:
            raise AppErrors.COURSE_ACCESS_DENIED

        if db_license.expires_at:
            expire_time = db_license.expires_at
            if expire_time.tzinfo is None:
                expire_time = expire_time.replace(tzinfo=timezone.utc)
            if expire_time < datetime.now(timezone.utc):
                raise AppErrors.LICENSE_EXPIRED

        course_query = await db.execute(
            select(Course).where(Course.id == course_id, Course.is_active)
        )
        course_obj = course_query.scalars().first()

        if not course_obj:
            raise AppErrors.COURSE_NOT_FOUND

        nodes_query = await db.execute(
            select(CourseNode)
            .options(selectinload(CourseNode.vault_item))
            .where(CourseNode.course_id == course_id)
            .order_by(CourseNode.sort_order)
        )
        all_nodes = nodes_query.scalars().all()

        nodes_dict = {}
        for node in all_nodes:
            nodes_dict[node.id] = {
                "id": node.id,
                "parent_id": node.parent_id,
                "item_type": node.item_type,
                "title": node.title,
                "sort_order": node.sort_order,
                "duration": node.duration,
                "attachment_url": node.attachment_url,
                "vault": {
                    "uuid": node.vault_item.uuid,
                    "file_hash": node.vault_item.file_hash,
                    "download_url": node.vault_item.download_url,
                }
                if node.vault_item
                else None,
                "children": [],
            }

        tree = []
        for node_id, node_data in nodes_dict.items():
            parent_id = node_data["parent_id"]
            if parent_id is None:
                tree.append(node_data)
            else:
                if parent_id in nodes_dict:
                    nodes_dict[parent_id]["children"].append(node_data)
                else:
                    tree.append(node_data)

        return {
            "id": course_obj.id,
            "title": course_obj.title,
            "watermark_text": course_obj.watermark_text,
            "watermark_color": course_obj.watermark_color,
            "tree": tree,
        }

    @staticmethod
    async def get_all_courses_admin(db: AsyncSession):
        courses_query = await db.execute(select(Course).order_by(Course.id.desc()))
        courses = courses_query.scalars().all()

        result = []
        for c in courses:
            students_query = await db.execute(
                select(func.count(License.id)).where(License.course_id == c.id)
            )
            students_count = students_query.scalar() or 0

            videos_query = await db.execute(
                select(func.count(CourseNode.id)).where(
                    CourseNode.course_id == c.id, CourseNode.item_type == "video"
                )
            )
            videos_count = videos_query.scalar() or 0

            result.append(
                {
                    "id": c.id,
                    "title": c.title,
                    "is_active": c.is_active,
                    "total_students": students_count,
                    "total_videos": videos_count,
                }
            )
        return result

    @staticmethod
    async def create_course(data: CourseCreate, db: AsyncSession):
        new_course = Course(
            title=data.title,
            watermark_text=data.watermark_text,
            watermark_color=data.watermark_color,
            is_active=data.is_active,
        )
        db.add(new_course)
        await db.commit()
        await db.refresh(new_course)
        return new_course

    @staticmethod
    async def update_course(course_id: int, data: CourseUpdate, db: AsyncSession):
        course_query = await db.execute(select(Course).where(Course.id == course_id))
        course = course_query.scalars().first()

        if not course:
            raise AppErrors.COURSE_NOT_FOUND

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(course, key, value)

        await db.commit()
        await db.refresh(course)
        return course

    @staticmethod
    async def delete_course(course_id: int, db: AsyncSession):
        course_query = await db.execute(select(Course).where(Course.id == course_id))
        course = course_query.scalars().first()
        if not course:
            raise AppErrors.COURSE_NOT_FOUND

        await db.delete(course)
        await db.commit()
        return {"status": "success", "message": "Course deleted permanently"}

    @staticmethod
    async def create_node(data: NodeCreate, db: AsyncSession):
        new_node = CourseNode(
            course_id=data.course_id,
            parent_id=data.parent_id,
            item_type=data.item_type,
            title=data.title,
            sort_order=data.sort_order,
            video_url=data.video_url,
            duration=data.duration,
            attachment_url=data.attachment_url,
            vault_id=data.vault_id,
        )
        db.add(new_node)
        await db.commit()
        await db.refresh(new_node)
        return {"status": "success", "node_id": new_node.id}

    @staticmethod
    async def update_node(node_id: int, data: NodeUpdate, db: AsyncSession):
        node_query = await db.execute(
            select(CourseNode).where(CourseNode.id == node_id)
        )
        node = node_query.scalars().first()
        if not node:
            raise Exception("Node missing from database")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(node, key, value)

        await db.commit()
        return {"status": "success"}

    @staticmethod
    async def delete_node(node_id: int, db: AsyncSession):
        node_query = await db.execute(
            select(CourseNode).where(CourseNode.id == node_id)
        )
        node = node_query.scalars().first()
        if not node:
            raise Exception("Node missing from database")

        await db.delete(node)
        await db.commit()
        return {"status": "success"}

    @staticmethod
    async def auto_build_course(data: AutoBuildRequest, db: AsyncSession):
        return {
            "status": "success",
            "message": f"Auto-build initiated for batch: {data.batch_name}",
        }
