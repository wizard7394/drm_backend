from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.player_service import PlayerService
from app.core.database import get_db, get_vault_db
from app.api.v1.client.dependencies import get_current_user
from app.schemas.client.player import VideoManifestResponse

router = APIRouter()


@router.get("/{course_id}/manifest/{video_id}", response_model=VideoManifestResponse)
async def get_video_manifest(
    course_id: int,
    video_id: int,
    db: AsyncSession = Depends(get_db),
    vault_db: AsyncSession = Depends(get_vault_db),
    current_user: User = Depends(get_current_user),
):
    return await PlayerService.get_video_manifest(
        course_id, video_id, current_user, db, vault_db
    )
