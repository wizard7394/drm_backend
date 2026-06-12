import asyncio
from sqlalchemy import text
from app.core.database import engine, Base

from app.models.user import User  # noqa: F401
from app.models.device import HardwareDevice  # noqa: F401
from app.models.license import License  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.course import Course, CourseNode  # noqa: F401


async def sync_database_architecture():
    print("Initiating database architecture sync...")

    async with engine.begin() as conn:
        print("Executing drop sequence for legacy linear tables...")
        await conn.execute(text("DROP TABLE IF EXISTS course_videos CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS course_sections CASCADE;"))

        print("Generating new adjacency list tree model (CourseNode)...")
        await conn.run_sync(Base.metadata.create_all)

    print("Database sync completed successfully! The new tree architecture is online.")


if __name__ == "__main__":
    asyncio.run(sync_database_architecture())
