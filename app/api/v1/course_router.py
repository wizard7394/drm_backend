from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.api.dependencies import get_db
from app.models.course import Course, CourseSection
from app.schemas.course import CourseSchema

router = APIRouter()

@router.get("/{course_id}", response_model=CourseSchema)
async def get_course_details(course_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(Course)
        .options(
            selectinload(Course.sections).selectinload(CourseSection.videos)
        )
        .where(Course.id == course_id, Course.is_active)
    )
    result = await db.execute(query)
    course_obj = result.scalars().first()

    if not course_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found or inactive.")
    
    return course_obj