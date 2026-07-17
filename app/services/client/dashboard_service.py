from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user import User
from app.models.license import License
from app.models.transaction import Transaction
from app.models.course import WatchedVideo


class ClientDashboardService:
    @staticmethod
    async def get_user_stats(
        current_user: User, main_db: AsyncSession, vault_db: AsyncSession
    ):
        licenses_query = await main_db.execute(
            select(func.count(License.id)).where(
                License.user_id == current_user.id, License.is_active
            )
        )
        total_active_licenses = licenses_query.scalar() or 0

        watched_query = await vault_db.execute(
            select(func.count(WatchedVideo.id)).where(
                WatchedVideo.user_id == current_user.id
            )
        )
        total_watched_videos = watched_query.scalar() or 0

        transactions_query = await main_db.execute(
            select(Transaction)
            .where(
                Transaction.user_id == current_user.id,
                Transaction.status == "completed",
            )
            .order_by(Transaction.id.desc())
            .limit(5)
        )
        recent_transactions = transactions_query.scalars().all()

        return {
            "total_active_licenses": total_active_licenses,
            "total_watched_videos": total_watched_videos,
            "recent_transactions": recent_transactions,
        }
