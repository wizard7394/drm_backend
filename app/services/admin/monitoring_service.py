from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.user import User
from app.models.device import Device
from app.models.hardware_reset import HardwareReset
from app.core.errors import AppErrors


class AdminMonitoringService:
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
    async def block_device(hardware_id: str, db: AsyncSession):
        stmt = select(Device).where(Device.hardware_id == hardware_id)
        res = await db.execute(stmt)
        device = res.scalars().first()

        if not device:
            raise AppErrors.DEVICE_NOT_FOUND

        device.is_blocked = True
        await db.commit()
        return {"status": "success", "message": "device_blocked_successfully"}

    @staticmethod
    async def get_pending_resets(db: AsyncSession):
        stmt = select(HardwareReset).where(HardwareReset.status == "pending")
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def approve_hardware_reset(request_id: int, admin_id: int, db: AsyncSession):
        stmt = select(HardwareReset).where(HardwareReset.id == request_id)
        res = await db.execute(stmt)
        reset_request = res.scalars().first()

        if not reset_request or reset_request.status != "pending":
            raise Exception("Invalid or non-pending reset request")

        dev_stmt = select(Device).where(Device.user_id == reset_request.user_id)
        dev_res = await db.execute(dev_stmt)
        devices = dev_res.scalars().all()

        for d in devices:
            await db.delete(d)

        reset_request.status = "approved"
        reset_request.approved_by_admin_id = admin_id
        await db.commit()

        return {"status": "success", "message": "hardware_reset_approved"}

    @staticmethod
    async def reject_hardware_reset(request_id: int, admin_id: int, db: AsyncSession):
        stmt = select(HardwareReset).where(HardwareReset.id == request_id)
        res = await db.execute(stmt)
        reset_request = res.scalars().first()

        if not reset_request or reset_request.status != "pending":
            raise Exception("Invalid or non-pending reset request")

        reset_request.status = "rejected"
        reset_request.approved_by_admin_id = admin_id
        await db.commit()

        return {"status": "success", "message": "hardware_reset_rejected"}
