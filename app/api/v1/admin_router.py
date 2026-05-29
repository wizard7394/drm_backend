from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db
from app.models.course import Course, CourseSection, CourseVideo
from app.schemas.admin import CreateCourseRequest, CreateSectionRequest, CreateVideoRequest

router = APIRouter()

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