import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine, Base

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


async def seed_video_keys():
    print("Checking and creating missing tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # ۱. ساخت کورس
        course_query = await session.execute(select(Course).where(Course.id == 13030))
        course = course_query.scalars().first()

        if not course:
            course = Course(id=13030, title="Premium Course 13030")
            session.add(course)
            await session.flush()

        # ۲. ساخت صندوقچه ویدیو (Vault) با تمام فیلدهای اجباری
        vault_query = await session.execute(
            select(VideoVault).where(VideoVault.id == 1)
        )
        vault = vault_query.scalars().first()

        aes_key = "iWHLiAQTRnKzj7DvTwB3Jly8RtHpZ0fBm9Ja8Jvl4ms="
        aes_iv = "wWFENQMtnBUbvaMl"

        if not vault:
            vault = VideoVault(
                id=1,
                course_id=13030,
                batch_name="seed_batch",  # <-- اضافه شد
                uuid="test-uuid-001",
                original_filename="dummy.mp4",  # <-- اضافه شد
                file_hash="dummy_hash_12345",  # <-- اضافه شد
                aes_key=aes_key,
                aes_iv=aes_iv,
                download_url="http://localhost/dummy.mp6",
                status="ready",  # <-- اضافه شد
            )
            session.add(vault)
            await session.flush()

        # ۳. ساخت نود درختی برای کورس
        node_query = await session.execute(select(CourseNode).where(CourseNode.id == 1))
        node = node_query.scalars().first()

        if not node:
            node = CourseNode(
                id=1,
                course_id=13030,
                title="01.Start",
                item_type="video",
                vault_id=vault.id,
            )
            session.add(node)

        await session.commit()
        print("Database updated successfully. Vault and Nodes injected.")


if __name__ == "__main__":
    asyncio.run(seed_video_keys())
