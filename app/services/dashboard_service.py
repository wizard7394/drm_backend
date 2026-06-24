import psutil
import platform
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.device import Device
from app.models.security_log import UnauthorizedAttempt


def get_naive_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


_cached_hardware_stats = {
    "cpu_usage": "0.0%",
    "ram_usage": "0.0GB / 0.0GB (0%)",
    "storage": "0.0GB / 0.0GB (0%)",
    "os": "Unknown",
}
_monitor_started = False


async def _hardware_monitor_daemon():
    psutil.cpu_percent(interval=None)

    while True:
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            ram_total = f"{ram.total / (1024**3):.1f}GB"
            ram_used = f"{ram.used / (1024**3):.3f}GB"

            disk_total = f"{disk.total / (1024**3):.1f}GB"
            disk_used = f"{disk.used / (1024**3):.3f}GB"

            try:
                os_info = platform.freedesktop_os_release()
                os_name = os_info.get(
                    "PRETTY_NAME", f"{platform.system()} {platform.release()}"
                )
            except Exception:
                os_name = f"{platform.system()} {platform.release()}"

            _cached_hardware_stats["cpu_usage"] = f"{cpu}%"
            _cached_hardware_stats["ram_usage"] = (
                f"{ram_used} / {ram_total} ({ram.percent}%)"
            )
            _cached_hardware_stats["storage"] = (
                f"{disk_used} / {disk_total} ({disk.percent}%)"
            )
            _cached_hardware_stats["os"] = os_name

        except Exception:
            pass

        await asyncio.sleep(2)


class DashboardService:
    @staticmethod
    async def get_full_stats(db: AsyncSession):
        global _monitor_started

        if not _monitor_started:
            asyncio.create_task(_hardware_monitor_daemon())
            _monitor_started = True

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

        return {
            "server": _cached_hardware_stats,
            "metrics": {
                "total_users": str(total_users),
                "online_users": str(online_users),
                "blocked_devices": str(blocked_devices),
                "failed_logins": str(failed_24h),
            },
        }
