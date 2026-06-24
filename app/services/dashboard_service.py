import psutil
import platform
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.device import Device
from app.models.security_log import UnauthorizedAttempt


def get_naive_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DashboardService:
    @staticmethod
    async def get_full_stats(db: AsyncSession):
        now = get_naive_utc_now()
        yesterday = now - timedelta(days=1)
        half_hour_ago = now - timedelta(minutes=30)

        total_users_query = await db.execute(select(func.count(User.id)))
        total_users = total_users_query.scalar() or 0

        online_query = await db.execute(
            select(func.count(Device.id)).where(Device.last_login >= half_hour_ago)
        )
        online_users = online_query.scalar() or 0

        blocked_query = await db.execute(
            select(func.count(Device.id)).where(Device.is_blocked)
        )
        blocked_devices = blocked_query.scalar() or 0

        failed_query = await db.execute(
            select(func.count(UnauthorizedAttempt.id)).where(
                UnauthorizedAttempt.attempted_at >= yesterday
            )
        )
        failed_24h = failed_query.scalar() or 0

        cpu_percent = psutil.cpu_percent(interval=0)

        ram = psutil.virtual_memory()
        ram_total = f"{ram.total / (1024**3):.1f}GB"
        ram_used = f"{ram.used / (1024**3):.1f}GB"

        disk = psutil.disk_usage("/")
        disk_total = f"{disk.total / (1024**3):.1f}GB"
        disk_used = f"{disk.used / (1024**3):.1f}GB"

        try:
            os_info = platform.freedesktop_os_release()
            os_name = os_info.get(
                "PRETTY_NAME", f"{platform.system()} {platform.release()}"
            )
        except Exception:
            os_name = f"{platform.system()} {platform.release()}"

        return {
            "server": {
                "cpu_usage": f"{cpu_percent}%",
                "ram_usage": f"{ram_used} / {ram_total}",
                "storage": f"{disk_used} / {disk_total}",
                "os": os_name,
            },
            "metrics": {
                "total_users": str(total_users),
                "online_users": str(online_users),
                "blocked_devices": str(blocked_devices),
                "failed_logins": str(failed_24h),
            },
        }
