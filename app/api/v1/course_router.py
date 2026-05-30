from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.api.dependencies import get_db, get_current_device
from app.models.course import Course, CourseSection
from app.models.license import License
from app.models.device import HardwareDevice
from app.schemas.course import CourseSchema

router = APIRouter()

@router.get("/{course_id}", response_model=CourseSchema)
async def get_course_details(
    course_id: int, 
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
            detail="Access denied. Your license does not cover this course."
        )

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







