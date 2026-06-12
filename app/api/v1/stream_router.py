import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
        select(CourseNode).where(
            CourseNode.id == video_id, CourseNode.item_type == "video"
        )
    )
    db_video = video_query.scalars().first()

    if not db_video or not db_video.aes_key or not db_video.aes_iv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encryption keys not found for this video.",
        )

    return {
        "status": "success",
        "video_id": video_id,
        "aes_key": db_video.aes_key,
        "aes_iv": db_video.aes_iv,
    }


@router.get("/{course_id}/vid_{video_id}/{file_name}")
async def stream_video(
    course_id: int,
    video_id: int,
    file_name: str,
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
            detail="Access denied for this course stream.",
        )

    base_path = f"media/hls/{course_id}/vid_{video_id}"
    file_path = os.path.join(base_path, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stream file not found."
        )

    return FileResponse(file_path, media_type="application/octet-stream")
