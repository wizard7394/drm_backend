from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.api.dependencies import get_db
from app.models.course import Course, CourseNode
from app.models.user import User
from app.models.license import License

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    courses_count = await db.scalar(select(func.count(Course.id)))
    folders_count = await db.scalar(
        select(func.count(CourseNode.id)).where(CourseNode.item_type == "folder")
    )
    videos_count = await db.scalar(
        select(func.count(CourseNode.id)).where(CourseNode.item_type == "video")
    )
    users_count = await db.scalar(select(func.count(User.id)))
    licenses_count = await db.scalar(select(func.count(License.id)))

    return {
        "status": "success",
        "stats": {
            "total_courses": courses_count or 0,
            "total_folders": folders_count or 0,
            "total_videos": videos_count or 0,
            "total_users": users_count or 0,
            "total_licenses": licenses_count or 0,
        },
    }
