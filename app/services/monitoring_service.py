from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.user import User
from app.models.device import Device
from app.models.hardware_reset import HardwareReset
from app.core.errors import AppErrors
from app.schemas.monitoring import BlockDeviceRequest, ResetHardwareRequest


class MonitoringService:
    @staticmethod
    async def get_user_devices(identifier: str, db: AsyncSession):
        stmt = select(User).where(
            or_(User.mobile == identifier, User.email == identifier)
        )
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise AppErrors.USER_NOT_FOUND

        dev_stmt = select(Device).where(Device.user_id == user.id)
        dev_res = await db.execute(dev_stmt)
        devices = dev_res.scalars().all()

        return {
            "id": user.id,
            "identifier": user.mobile or user.email or "",
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "devices": devices,
        }

    @staticmethod
    async def block_device(payload: BlockDeviceRequest, db: AsyncSession):
        stmt = select(Device).where(Device.hardware_id == payload.hardware_id)
        res = await db.execute(stmt)
        device = res.scalars().first()

        if not device:
            raise AppErrors.DEVICE_NOT_FOUND

        device.is_blocked = True
        await db.commit()
        return {"status": "success", "message": "device_blocked_successfully"}

    @staticmethod
    async def reset_hardware(
        payload: ResetHardwareRequest, admin_id: int, db: AsyncSession
    ):
        stmt = select(User).where(
            or_(User.mobile == payload.identifier, User.email == payload.identifier)
        )
        res = await db.execute(stmt)
        user = res.scalars().first()

        if not user:
            raise AppErrors.USER_NOT_FOUND

        dev_stmt = select(Device).where(Device.user_id == user.id)
        dev_res = await db.execute(dev_stmt)
        devices = dev_res.scalars().all()

        for d in devices:
            reset_log = HardwareReset(
                user_id=user.id,
                previous_hardware_id=d.hardware_id,
                reason=payload.reason,
                approved_by_admin_id=admin_id,
            )
            db.add(reset_log)
            await db.delete(d)

        await db.commit()
        return {"status": "success", "message": "hardware_reset_successful"}
