from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.course import Course, CourseNode
from app.models.user import User
from app.models.license import License


class DashboardService:
    @staticmethod
    async def get_admin_stats(db: AsyncSession):
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
            "total_courses": courses_count or 0,
            "total_folders": folders_count or 0,
            "total_videos": videos_count or 0,
            "total_users": users_count or 0,
            "total_licenses": licenses_count or 0,
        }

    @staticmethod
    async def get_user_courses(current_user: User, db: AsyncSession):
        query = await db.execute(
            select(Course)
            .join(License, License.course_id == Course.id)
            .where(License.user_id == current_user.id, License.is_active)
        )
        courses = query.scalars().all()

        return [
            {"id": c.id, "title": c.title, "watermark_text": c.watermark_text}
            for c in courses
        ]
