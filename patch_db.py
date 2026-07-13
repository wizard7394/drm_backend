import asyncio
from sqlalchemy import text
from app.core.database import vault_engine


async def add_missing_column():
    print("Injecting aes_iv column to PostgreSQL...")
    async with vault_engine.begin() as conn:
        try:
            # دستور مستقیم برای اضافه کردن ستون به دیتابیس
            await conn.execute(
                text("ALTER TABLE vault_items ADD COLUMN aes_iv VARCHAR;")
            )
            print("✅ Column 'aes_iv' successfully added!")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(add_missing_column())
