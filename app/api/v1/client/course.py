from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.services.course_service import CourseService
from app.core.database import get_db, get_vault_db
from app.api.v1.client.dependencies import get_current_user
from app.schemas.course import (
    ClientCourseListResponse,
    ClientCourseDetailsResponse,
    WatchedVideoResponse,
    WatchedVideosListResponse,
)

router = APIRouter()


@router.get("/my-courses", response_model=ClientCourseListResponse)
async def get_user_courses(
    db: AsyncSession = Depends(get_db),
    vault_db: AsyncSession = Depends(get_vault_db),
    current_user: User = Depends(get_current_user),
):
    return await CourseService.get_user_courses(current_user, db, vault_db)


@router.get("/view/{course_id}", response_model=ClientCourseDetailsResponse)
async def get_course_details(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    vault_db: AsyncSession = Depends(get_vault_db),
    current_user: User = Depends(get_current_user),
):
    return await CourseService.get_course_details(course_id, current_user, db, vault_db)


@router.post("/watched/{vault_uuid}", response_model=WatchedVideoResponse)
async def mark_video_watched(
    vault_uuid: str,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_user: User = Depends(get_current_user),
):
    return await CourseService.mark_video_watched(vault_uuid, current_user, vault_db)


@router.get("/watched", response_model=WatchedVideosListResponse)
async def get_watched_videos(
    vault_db: AsyncSession = Depends(get_vault_db),
    current_user: User = Depends(get_current_user),
):
    return await CourseService.get_watched_videos(current_user, vault_db)
