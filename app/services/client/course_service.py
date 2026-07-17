from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.course import Course, CourseNode, WatchedVideo
from app.models.license import License
from app.models.user import User
from app.core.errors import AppErrors


class ClientCourseService:
    @staticmethod
    async def get_user_courses(
        current_user: User, db: AsyncSession, vault_db: AsyncSession
    ):
        stmt = select(License.course_id).where(
            License.user_id == current_user.id, License.is_active
        )
        license_result = await db.execute(stmt)
        course_ids = license_result.scalars().all()

        if not course_ids:
            return {"status": "success", "courses": []}

        course_stmt = select(Course).where(Course.id.in_(course_ids), Course.is_active)
        course_result = await vault_db.execute(course_stmt)
        courses = course_result.scalars().all()

        course_list = [
            {"id": c.id, "title": c.title, "is_active": bool(c.is_active)}
            for c in courses
        ]
        return {"status": "success", "courses": course_list}

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
                "attachments": node.attachments,
                "vault": {
                    "uuid": node.vault_item.uuid,
                    "file_hash": node.vault_item.file_hash,
                    "download_url": node.vault_item.download_url,
                }
                if getattr(node, "vault_item", None)
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
            "sections": tree,
        }

    @staticmethod
    async def mark_video_watched(
        vault_uuid: str, current_user: User, vault_db: AsyncSession
    ):
        stmt = select(WatchedVideo).where(
            WatchedVideo.user_id == current_user.id,
            WatchedVideo.vault_uuid == vault_uuid,
        )
        result = await vault_db.execute(stmt)
        existing = result.scalars().first()

        if not existing:
            new_watched = WatchedVideo(user_id=current_user.id, vault_uuid=vault_uuid)
            vault_db.add(new_watched)
            await vault_db.commit()

        return {"status": "success"}

    @staticmethod
    async def get_watched_videos(current_user: User, vault_db: AsyncSession):
        stmt = select(WatchedVideo.vault_uuid).where(
            WatchedVideo.user_id == current_user.id
        )
        result = await vault_db.execute(stmt)
        watched_uuids = result.scalars().all()

        return {"status": "success", "watched_uuids": watched_uuids}
