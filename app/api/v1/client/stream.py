from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_vault_db, get_current_user
from app.models.user import User
from app.services.stream_service import StreamService

router = APIRouter()


@router.get("/{course_id}/vid_{video_id}/keys")
async def get_video_keys(
    course_id: int,
    video_id: int,
    db: AsyncSession = Depends(get_db),
    vault_db: AsyncSession = Depends(get_vault_db),
    current_user: User = Depends(get_current_user),
):
    return await StreamService.get_video_keys(
        course_id, video_id, current_user, db, vault_db
    )
