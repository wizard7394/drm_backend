from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.client.player_service import ClientPlayerService
from app.core.database import get_db, get_vault_db
from app.api.v1.client.dependencies import get_current_user
from app.schemas.client.player import VideoManifestResponse

router = APIRouter()


@router.get("/{course_id}/manifest/{video_id}", response_model=VideoManifestResponse)
async def get_video_manifest(
    course_id: int,
    video_id: int,
    hardware_id: str = Header(..., alias="X-Hardware-Id"),
    db: AsyncSession = Depends(get_db),
    vault_db: AsyncSession = Depends(get_vault_db),
    current_user: User = Depends(get_current_user),
):
    return await ClientPlayerService.get_video_manifest(
        course_id=course_id,
        video_id=video_id,
        hardware_id=hardware_id,
        current_user=current_user,
        main_db=db,
        vault_db=vault_db,
    )
