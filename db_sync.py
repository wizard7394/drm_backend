import asyncio
from sqlalchemy import text
from app.core.database import engine, Base

from app.models.user import User  # noqa: F401
from app.models.device import HardwareDevice  # noqa: F401
from app.models.license import License  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.vault import VideoVault  # noqa: F401
from app.models.course import Course, CourseNode  # noqa: F401


async def sync_database_architecture():
    print("Initiating global database architecture sync for Video Vault...")

    async with engine.begin() as conn:
        print("Executing drop sequence for outdated course structures...")
        await conn.execute(text("DROP TABLE IF EXISTS course_nodes CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS video_vault CASCADE;"))

        print("Generating new Vault-connected tree architecture...")
        await conn.run_sync(Base.metadata.create_all)

    print("Database sync completed! The Video Vault and Node tables are online.")


if __name__ == "__main__":
    asyncio.run(sync_database_architecture())
