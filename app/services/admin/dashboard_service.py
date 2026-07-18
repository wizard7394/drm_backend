import platform
import psutil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user import User
from app.models.course import Course
from app.models.license import License
from app.models.transaction import Transaction
from app.models.security_log import UnauthorizedAttempt, BlacklistedHardware


class AdminDashboardService:
    @staticmethod
    async def get_stats(main_db: AsyncSession, vault_db: AsyncSession):
        users_query = await main_db.execute(select(func.count(User.id)))
        total_users = users_query.scalar() or 0

        courses_query = await vault_db.execute(
            select(func.count(Course.id)).where(Course.is_active == 1)
        )
        total_courses = courses_query.scalar() or 0

        licenses_query = await main_db.execute(
            select(func.count(License.id)).where(License.is_active.is_(True))
        )
        total_active_licenses = licenses_query.scalar() or 0

        revenue_query = await main_db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.status == "completed"
            )
        )
        total_revenue = revenue_query.scalar() or 0

        logs_query = await main_db.execute(
            select(UnauthorizedAttempt)
            .order_by(UnauthorizedAttempt.id.desc())
            .limit(10)
        )
        recent_logs = logs_query.scalars().all()

        failed_logins_query = await main_db.execute(
            select(func.count(UnauthorizedAttempt.id))
        )
        failed_logins = failed_logins_query.scalar() or 0

        blocked_query = await main_db.execute(
            select(func.count(BlacklistedHardware.id))
        )
        blocked_devices = blocked_query.scalar() or 0

        cpu_usage = f"{psutil.cpu_percent()}%"

        ram = psutil.virtual_memory()
        ram_usage = f"{int(ram.used / (1024**3))}GB"

        disk = psutil.disk_usage("/")
        storage = f"{int(disk.used / (1024**3))}GB"

        system_os = f"{platform.system()} {platform.release()}"

        online_users = 0

        return {
            "total_users": total_users,
            "total_courses": total_courses,
            "total_active_licenses": total_active_licenses,
            "total_revenue": total_revenue,
            "recent_logs": recent_logs,
            "cpu_usage": cpu_usage,
            "ram_usage": ram_usage,
            "storage": storage,
            "system_os": system_os,
            "online_users": online_users,
            "blocked_devices": blocked_devices,
            "failed_logins": failed_logins,
        }
