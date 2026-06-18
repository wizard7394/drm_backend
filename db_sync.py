import asyncio
from sqlalchemy import text
from app.core.database import engine, Base

# === Import ALL models to register them in SQLAlchemy ===
from app.models.user import User
from app.models.admin import Admin
from app.models.device import Device
from app.models.hardware_reset import HardwareReset
from app.models.license import License
from app.models.transaction import Transaction
from app.models.vault import VideoVault
from app.models.course import Course, CourseNode
from app.models.security_log import UnauthorizedAttempt, BlacklistedHardware


async def sync_database_architecture():
    print("Initiating global database architecture sync for Postgres...")

    async with engine.begin() as conn:
        print("Executing DROP ALL TABLES sequence...")
        await conn.run_sync(Base.metadata.drop_all)

        print("Generating new Vault-connected tree architecture and Security Logs...")
        await conn.run_sync(Base.metadata.create_all)

    print("Database sync completed! All tables are online.")


if __name__ == "__main__":
    asyncio.run(sync_database_architecture())
