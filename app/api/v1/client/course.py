from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db, get_vault_db, get_current_user
from app.models.user import User
from app.services.course_service import CourseService

router = APIRouter()


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
