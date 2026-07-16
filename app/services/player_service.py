from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from app.models.course import CourseNode
from app.models.license import License
from app.models.user import User
from app.core.errors import AppErrors


class PlayerService:
    @staticmethod
    async def get_video_manifest(
        course_id: int,
        video_id: int,
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
