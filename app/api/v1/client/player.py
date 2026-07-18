from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.client.player_service import ClientPlayerService
from app.core.database import get_db, get_vault_db
from app.api.v1.client.dependencies import get_current_user
from app.schemas.client.player import VideoManifestResponse

router = APIRouter()


@router.get("/{course_id}/manifest/{vault_uuid}", response_model=VideoManifestResponse)
async def get_video_manifest(
    course_id: int,
    vault_uuid: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    vault_db: AsyncSession = Depends(get_vault_db),
    current_user: User = Depends(get_current_user),
):
    hardware_id = request.headers.get("x-hardware-id")

    if not hardware_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Hardware-Id header",
        )

    return await ClientPlayerService.get_video_manifest(
        course_id=course_id,
        vault_uuid=vault_uuid,
        hardware_id=hardware_id,
        current_user=current_user,
        main_db=db,
        vault_db=vault_db,
    )
