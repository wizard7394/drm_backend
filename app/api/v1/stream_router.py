from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.api.dependencies import get_db, get_current_device
from app.models.license import License
from app.models.device import HardwareDevice
from app.models.course import CourseNode

router = APIRouter()


@router.get("/{course_id}/vid_{video_id}/keys")
async def get_video_keys(
    course_id: int,
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_device: HardwareDevice = Depends(get_current_device),
):
    license_query = await db.execute(
        select(License).where(License.id == current_device.license_id)
    )
    db_license = license_query.scalars().first()

    if not db_license or db_license.course_id != course_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this encryption keys request.",
        )

    video_query = await db.execute(
        select(CourseNode)
        .options(selectinload(CourseNode.vault_item))
        .where(CourseNode.id == video_id, CourseNode.item_type == "video")
    )
    db_video = video_query.scalars().first()

    if not db_video or not db_video.vault_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encryption keys not found for this video.",
        )

    return {
        "status": "success",
        "video_id": video_id,
        "uuid": db_video.vault_item.uuid,
        "file_hash": db_video.vault_item.file_hash,
        "aes_key": db_video.vault_item.aes_key,
        "aes_iv": db_video.vault_item.aes_iv,
    }
