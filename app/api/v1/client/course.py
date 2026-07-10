from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db, get_vault_db, get_current_user
from app.models.user import User
from app.services.course_service import CourseService

from sqlalchemy import select
from app.models.license import License
from app.models.course import Course

router = APIRouter()


@router.get("/my-courses")
async def get_user_courses(
    db: AsyncSession = Depends(get_db),
    vault_db: AsyncSession = Depends(get_vault_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(License.course_id).where(
        License.user_id == current_user.id, License.is_active
    )

    license_result = await db.execute(stmt)
    course_ids = license_result.scalars().all()

    if not course_ids:
        return {"status": "success", "courses": []}

    course_stmt = select(Course).where(Course.id.in_(course_ids), Course.is_active == 1)
    course_result = await vault_db.execute(course_stmt)
    courses = course_result.scalars().all()

    course_list = [
        {"id": c.id, "title": c.title, "is_active": bool(c.is_active)} for c in courses
    ]

    return {"status": "success", "courses": course_list}


@router.get("/view/{course_id}")
async def get_course_details(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    vault_db: AsyncSession = Depends(get_vault_db),
    current_user: User = Depends(get_current_user),
):
    return await CourseService.get_course_details(course_id, current_user, db, vault_db)


@router.post("/watched/{vault_uuid}")
async def mark_video_watched(
    vault_uuid: str,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.course import WatchedVideo
    from sqlalchemy import select

    stmt = select(WatchedVideo).where(
        WatchedVideo.user_id == current_user.id, WatchedVideo.vault_uuid == vault_uuid
    )
    result = await vault_db.execute(stmt)
    existing = result.scalars().first()

    if not existing:
        new_watched = WatchedVideo(user_id=current_user.id, vault_uuid=vault_uuid)
        vault_db.add(new_watched)
        await vault_db.commit()

    return {"status": "success"}


@router.get("/watched")
async def get_watched_videos(
    vault_db: AsyncSession = Depends(get_vault_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.course import WatchedVideo
    from sqlalchemy import select

    stmt = select(WatchedVideo.vault_uuid).where(
        WatchedVideo.user_id == current_user.id
    )
    result = await vault_db.execute(stmt)
    watched_uuids = result.scalars().all()

    return {"status": "success", "watched_uuids": watched_uuids}
