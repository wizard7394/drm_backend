import asyncio
from app.core.database import engine, Base


async def reset_database():
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    print("Creating all tables from current models...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database reset completed successfully.")


if __name__ == "__main__":
    asyncio.run(reset_database())
