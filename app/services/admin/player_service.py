from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.course import CourseNode
from app.core.errors import AppErrors


class AdminPlayerService:
    @staticmethod
    async def get_video_manifest(
        course_id: int,
        video_id: int,
        vault_db: AsyncSession,
    ):
        video_query = await vault_db.execute(
            select(CourseNode)
            .options(selectinload(CourseNode.vault_item))
            .where(
                CourseNode.id == video_id,
                CourseNode.course_id == course_id,
                CourseNode.item_type == "video",
            )
        )
        db_video = video_query.scalars().first()

        if not db_video or not db_video.vault_item:
            raise AppErrors.VIDEO_KEYS_NOT_FOUND

        v_item = db_video.vault_item
        aes_key = getattr(v_item, "aes_key", getattr(v_item, "decryption_key", None))
        aes_iv = getattr(v_item, "aes_iv", None)

        return {
            "status": "success",
            "video_id": video_id,
            "uuid": v_item.uuid,
            "file_hash": v_item.file_hash,
            "aes_key": aes_key,
            "aes_iv": aes_iv,
        }
