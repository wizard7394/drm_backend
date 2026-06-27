import asyncio
from sqlalchemy import text  # noqa: F401
from app.core.database import engine, Base, vault_engine, VaultBase

from app.models.user import User  # noqa: F401
from app.models.admin import Admin  # noqa: F401
from app.models.device import Device  # noqa: F401
from app.models.hardware_reset import HardwareReset  # noqa: F401
from app.models.license import License  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.vault import VaultItem  # noqa: F401
from app.models.course import Course, CourseNode  # noqa: F401
from app.models.security_log import (
    UnauthorizedAttempt,  # noqa: F401
    BlacklistedHardware,  # noqa: F401
    DeviceAuditLog,  # noqa: F401
)


async def sync_database_architecture():
    print("Initiating global database architecture sync for Postgres...")

    async with engine.begin() as conn:
        print("Executing DROP ALL TABLES sequence for Main DB...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Generating new Main DB architecture...")
        await conn.run_sync(Base.metadata.create_all)

    async with vault_engine.begin() as conn:
        print("Executing DROP ALL TABLES sequence for Vault DB...")
        await conn.run_sync(VaultBase.metadata.drop_all)
        print("Generating new Vault DB architecture...")
        await conn.run_sync(VaultBase.metadata.create_all)

    print("Database sync completed! All tables are online.")


if __name__ == "__main__":
    asyncio.run(sync_database_architecture())
