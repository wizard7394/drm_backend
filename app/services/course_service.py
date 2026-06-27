from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from app.models.course import Course, CourseNode
from app.models.license import License
from app.models.user import User
from app.models.vault import VaultItem
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
    async def get_course_details(
        course_id: int,
        current_user: User,
        main_db: AsyncSession,
        vault_db: AsyncSession,
    ):
        license_query = await main_db.execute(
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

        course_query = await vault_db.execute(
            select(Course).where(Course.id == course_id, Course.is_active)
        )
        course_obj = course_query.scalars().first()

        if not course_obj:
            raise AppErrors.COURSE_NOT_FOUND

        nodes_query = await vault_db.execute(
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
    async def get_all_courses_admin(vault_db: AsyncSession, main_db: AsyncSession):
        courses_query = await vault_db.execute(
            select(Course).order_by(Course.id.desc())
        )
        courses = courses_query.scalars().all()

        result = []
        for c in courses:
            students_query = await main_db.execute(
                select(func.count(License.id)).where(License.course_id == c.id)
            )
            students_count = students_query.scalar() or 0

            videos_query = await vault_db.execute(
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
    async def get_course_tree_admin(course_id: int, vault_db: AsyncSession):
        course_query = await vault_db.execute(
            select(Course).where(Course.id == course_id)
        )
        course_obj = course_query.scalars().first()

        if not course_obj:
            raise AppErrors.COURSE_NOT_FOUND

        nodes_query = await vault_db.execute(
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
    async def create_course(data: CourseCreate, vault_db: AsyncSession):
        new_course = Course(
            title=data.title,
            watermark_text=data.watermark_text,
            watermark_color=data.watermark_color,
            is_active=data.is_active,
        )
        vault_db.add(new_course)
        await vault_db.commit()
        await vault_db.refresh(new_course)
        return new_course

    @staticmethod
    async def update_course(course_id: int, data: CourseUpdate, vault_db: AsyncSession):
        course_query = await vault_db.execute(
            select(Course).where(Course.id == course_id)
        )
        course = course_query.scalars().first()

        if not course:
            raise AppErrors.COURSE_NOT_FOUND

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(course, key, value)

        await vault_db.commit()
        await vault_db.refresh(course)
        return course

    @staticmethod
    async def delete_course(course_id: int, vault_db: AsyncSession):
        course_query = await vault_db.execute(
            select(Course).where(Course.id == course_id)
        )
        course = course_query.scalars().first()
        if not course:
            raise AppErrors.COURSE_NOT_FOUND

        await vault_db.delete(course)
        await vault_db.commit()
        return {"status": "success", "message": "Course deleted permanently"}

    @staticmethod
    async def create_node(data: NodeCreate, vault_db: AsyncSession):
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
        vault_db.add(new_node)
        await vault_db.commit()
        await vault_db.refresh(new_node)
        return {"status": "success", "node_id": new_node.id}

    @staticmethod
    async def update_node(node_id: int, data: NodeUpdate, vault_db: AsyncSession):
        node_query = await vault_db.execute(
            select(CourseNode).where(CourseNode.id == node_id)
        )
        node = node_query.scalars().first()
        if not node:
            raise Exception("Node missing from database")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(node, key, value)

        await vault_db.commit()
        return {"status": "success"}

    @staticmethod
    async def delete_node(node_id: int, vault_db: AsyncSession):
        node_query = await vault_db.execute(
            select(CourseNode).where(CourseNode.id == node_id)
        )
        node = node_query.scalars().first()
        if not node:
            raise Exception("Node missing from database")

        await vault_db.delete(node)
        await vault_db.commit()
        return {"status": "success"}

    @staticmethod
    async def auto_build_course(data: AutoBuildRequest, vault_db: AsyncSession):
        return {
            "status": "success",
            "message": f"Auto-build initiated for batch: {data.batch_name}",
        }

    @staticmethod
    async def export_vault_data(vault_db: AsyncSession):
        courses = (await vault_db.execute(select(Course))).scalars().all()
        nodes = (
            (
                await vault_db.execute(
                    select(CourseNode).options(selectinload(CourseNode.vault_item))
                )
            )
            .scalars()
            .all()
        )

        export_data = {"courses": [], "nodes": []}
        for c in courses:
            export_data["courses"].append(
                {
                    "id": c.id,
                    "title": c.title,
                    "watermark_text": c.watermark_text,
                    "watermark_color": c.watermark_color,
                    "is_active": c.is_active,
                }
            )

        for n in nodes:
            nd = {
                "id": n.id,
                "course_id": n.course_id,
                "parent_id": n.parent_id,
                "item_type": n.item_type,
                "title": n.title,
                "sort_order": n.sort_order,
                "video_url": n.video_url,
                "duration": n.duration,
                "attachment_url": n.attachment_url,
                "vault_item": None,
            }
            if n.vault_item:
                nd["vault_item"] = {
                    "uuid": n.vault_item.uuid,
                    "file_hash": n.vault_item.file_hash,
                    "download_url": n.vault_item.download_url,
                    "decryption_key": n.vault_item.decryption_key,
                }
            export_data["nodes"].append(nd)

        return export_data

    @staticmethod
    async def import_vault_data(data: dict, vault_db: AsyncSession):
        await vault_db.execute(text("DELETE FROM course_nodes"))
        await vault_db.execute(text("DELETE FROM courses"))
        await vault_db.execute(text("DELETE FROM vault_items"))

        for c_data in data.get("courses", []):
            course = Course(
                id=c_data["id"],
                title=c_data["title"],
                watermark_text=c_data.get("watermark_text"),
                watermark_color=c_data.get("watermark_color", "rgba(255,255,255,0.3)"),
                is_active=c_data.get("is_active", True),
            )
            vault_db.add(course)

        for n_data in data.get("nodes", []):
            vault_item_id = None
            v_data = n_data.get("vault_item")
            if v_data:
                vault_item = VaultItem(
                    uuid=v_data["uuid"],
                    file_hash=v_data["file_hash"],
                    download_url=v_data["download_url"],
                    decryption_key=v_data["decryption_key"],
                )
                vault_db.add(vault_item)
                await vault_db.flush()
                vault_item_id = vault_item.id

            node = CourseNode(
                id=n_data["id"],
                course_id=n_data["course_id"],
                parent_id=n_data["parent_id"],
                item_type=n_data["item_type"],
                title=n_data["title"],
                sort_order=n_data.get("sort_order", 0),
                video_url=n_data.get("video_url"),
                duration=n_data.get("duration"),
                attachment_url=n_data.get("attachment_url"),
                vault_id=vault_item_id,
            )
            vault_db.add(node)

        await vault_db.commit()
        return {
            "status": "success",
            "message": "Vault successfully imported and restored.",
        }
