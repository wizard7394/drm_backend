from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.api.dependencies import get_db
from app.models.course import Course, CourseSection, CourseVideo
from app.schemas.admin import CreateCourseRequest, CreateSectionRequest, CreateVideoRequest

router = APIRouter()

class KeySyncPayload(BaseModel):
    video_id: int
    aes_key: str
    aes_iv: str

@router.post("/course", status_code=status.HTTP_201_CREATED)
async def create_course(request: CreateCourseRequest, db: AsyncSession = Depends(get_db)):
    new_course = Course(
        title=request.title,
        watermark_text=request.watermark_text,
        watermark_color=request.watermark_color
    )
    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)
    return {"status": "success", "course_id": new_course.id}

@router.post("/section", status_code=status.HTTP_201_CREATED)
async def create_section(request: CreateSectionRequest, db: AsyncSession = Depends(get_db)):
    new_section = CourseSection(
        course_id=request.course_id,
        title=request.title,
        sort_order=request.sort_order
    )
    db.add(new_section)
    await db.commit()
    await db.refresh(new_section)
    return {"status": "success", "section_id": new_section.id}

@router.post("/video", status_code=status.HTTP_201_CREATED)
async def create_video(request: CreateVideoRequest, db: AsyncSession = Depends(get_db)):
    new_video = CourseVideo(
        section_id=request.section_id,
        title=request.title,
        duration=request.duration,
        video_url=request.video_url,
        sort_order=request.sort_order
    )
    db.add(new_video)
    await db.commit()
    await db.refresh(new_video)
    return {"status": "success", "video_id": new_video.id}

@router.post("/keys/sync", status_code=status.HTTP_200_OK)
async def sync_video_keys(payload: KeySyncPayload, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(CourseVideo).where(CourseVideo.id == payload.video_id))
    db_video = query.scalars().first()
    
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found")
        
    db_video.aes_key = payload.aes_key
    db_video.aes_iv = payload.aes_iv
    
    try:
        await db.commit()
        return {"status": "success", "message": "Encryption keys synced securely."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))