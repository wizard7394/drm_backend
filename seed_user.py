import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal

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


async def seed_test_user():
    async with AsyncSessionLocal() as session:
        test_phone = "09367013231"

        user_query = await session.execute(
            select(User).where(User.mobile == test_phone)
        )
        user = user_query.scalars().first()

        if not user:
            user = User(mobile=test_phone, is_active=True)
            session.add(user)
            await session.flush()
            print("Test user created successfully.")

        license_query = await session.execute(
            select(License).where(
                License.user_id == user.id, License.course_id == 13030
            )
        )
        lic = license_query.scalars().first()

        if not lic:
            lic = License(
                user_id=user.id,
                course_id=13030,
                license_key="PREMIUM-LIC-13030",
                is_active=True,  # <--- اینجا اصلاح شد
            )
            session.add(lic)
            print("Premium license assigned to test user.")

        await session.commit()
        print("Database sync complete.")


if __name__ == "__main__":
    asyncio.run(seed_test_user())
