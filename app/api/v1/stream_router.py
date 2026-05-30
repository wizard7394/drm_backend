import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.dependencies import get_db, get_current_device
from app.models.license import License
from app.models.device import HardwareDevice

router = APIRouter()

@router.get("/{course_id}/vid_{video_id}/{file_name}")
async def stream_video(
    course_id: int,
    video_id: int,
    file_name: str,
    db: AsyncSession = Depends(get_db),
    current_device: HardwareDevice = Depends(get_current_device)
):
    license_query = await db.execute(
        select(License).where(License.id == current_device.license_id)
    )
    db_license = license_query.scalars().first()

    if not db_license or db_license.course_id != course_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this course stream."
        )

    base_path = f"media/hls/{course_id}/vid_{video_id}"
    file_path = os.path.join(base_path, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stream file not found.")

    return FileResponse(file_path, media_type="application/vnd.apple.mpegurl")