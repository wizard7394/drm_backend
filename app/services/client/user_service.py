from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.transaction import Transaction
from app.models.course import Course, WatchedVideo
from app.models.license import License


class ClientUserService:
    @staticmethod
    async def get_my_profile(current_user: User):
        return {
            "id": current_user.id,
            "mobile": current_user.mobile,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "email": current_user.email,
            "is_active": current_user.is_active,
        }

    @staticmethod
    async def get_my_heatmap(current_user: User, vault_db: AsyncSession):
        query = await vault_db.execute(
            select(WatchedVideo).where(WatchedVideo.user_id == current_user.id)
        )
        watched_logs = query.scalars().all()
        return {
            "heatmap": [
                {"vault_uuid": w.vault_uuid, "watched_at": w.watched_at}
                for w in watched_logs
            ]
        }

    @staticmethod
    async def get_my_transactions(current_user: User, db: AsyncSession):
        query = await db.execute(
            select(Transaction).where(Transaction.user_id == current_user.id)
        )
        transactions = query.scalars().all()
        return {
            "transactions": [
                {
                    "id": t.id,
                    "amount": getattr(t, "amount", 0),
                    "status": getattr(t, "status", "unknown"),
                }
                for t in transactions
            ]
        }

    @staticmethod
    async def get_my_courses(
        current_user: User, db: AsyncSession, vault_db: AsyncSession
    ):
        stmt = select(License.course_id).where(
            License.user_id == current_user.id, License.is_active
        )
        result = await db.execute(stmt)
        course_ids = result.scalars().all()

        if not course_ids:
            return {"courses": []}

        course_stmt = select(Course).where(Course.id.in_(course_ids))
        course_res = await vault_db.execute(course_stmt)
        courses = course_res.scalars().all()

        return {"courses": [{"id": c.id, "title": c.title} for c in courses]}
