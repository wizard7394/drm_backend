import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine

from app.models.user import User
from app.models.hardware_reset import HardwareReset
from app.models.license import License
from app.models.device import Device
from app.models.transaction import Transaction
from app.models.security_log import (
    UnauthorizedAttempt,
    BlacklistedHardware,
    DeviceAuditLog,
)


async def run_seed():
    async with AsyncSession(engine) as session:
        try:
            new_user = User(
                mobile="09367013231",
                first_name="Test",
                last_name="User",
                is_active=True,
                violation_count=0,
            )
            session.add(new_user)
            await session.commit()
            print("Test user created successfully in Main DB.")
        except Exception as e:
            await session.rollback()
            print(f"Error creating user: {e}")


if __name__ == "__main__":
    asyncio.run(run_seed())
