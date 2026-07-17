from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.device import Device
from app.models.hardware_reset import HardwareReset


class ClientMonitoringService:
    @staticmethod
    async def get_my_devices(current_user: User, db: AsyncSession):
        stmt = select(Device).where(Device.user_id == current_user.id)
        result = await db.execute(stmt)
        devices = result.scalars().all()
        return {"status": "success", "devices": devices}

    @staticmethod
    async def request_hardware_reset(current_user: User, reason: str, db: AsyncSession):
        stmt = select(HardwareReset).where(
            HardwareReset.user_id == current_user.id, HardwareReset.status == "pending"
        )
        result = await db.execute(stmt)
        existing_request = result.scalars().first()

        if existing_request:
            raise Exception("You already have a pending hardware reset request.")

        new_request = HardwareReset(
            user_id=current_user.id, reason=reason, status="pending"
        )
        db.add(new_request)
        await db.commit()

        return {"status": "success", "message": "reset_request_submitted_successfully"}
