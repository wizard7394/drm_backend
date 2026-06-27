from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import selectinload
from app.api.dependencies import get_db, get_vault_db, get_current_admin
from app.core.errors import AppErrors
from app.models.admin import Admin
from app.models.course import Course
from app.models.vault import VaultItem
from app.models.device import Device
from app.models.security_log import BlacklistedHardware, DeviceAuditLog
from app.models.hardware_reset import HardwareReset  # noqa: F401
from app.models.license import License  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.user import User

router = APIRouter()


class VaultItemPayload(BaseModel):
    uuid: str
    file_hash: str
    aes_key: str
    aes_iv: str
    original_filename: Optional[str] = None


class VaultBulkUploadRequest(BaseModel):
    course_id: int
    batch_name: str
    items: List[VaultItemPayload]


class BlockDeviceRequest(BaseModel):
    is_blocked: bool
    reason: str


class UnblockRequest(BaseModel):
    reason: str


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    vault_db: AsyncSession = Depends(get_vault_db),
    admin: Admin = Depends(get_current_admin),
):
    users_count = await db.execute(select(func.count(User.id)))
    devices_count = await db.execute(select(func.count(Device.id)))
    courses_count = await vault_db.execute(select(func.count(Course.id)))

    return {
        "status": "success",
        "total_users": users_count.scalar() or 0,
        "total_courses": courses_count.scalar() or 0,
        "total_devices": devices_count.scalar() or 0,
    }


@router.get("/devices")
async def get_all_devices(
    db: AsyncSession = Depends(get_db), admin: Admin = Depends(get_current_admin)
):
    query = await db.execute(
        select(Device, User.mobile)
        .join(User, Device.user_id == User.id)
        .order_by(Device.last_login.desc())
    )
    result = []
    for device, mobile in query.all():
        result.append(
            {
                "id": device.id,
                "hardware_id": device.hardware_id,
                "short_hash": device.hardware_id[:12] + "...",
                "system_specs": device.system_specs or "مشخصات ثبت نشده",
                "mobile": mobile,
                "is_blocked": device.is_blocked,
                "last_login": device.last_login,
            }
        )
    return {"devices": result}


@router.get("/security/blacklist")
async def get_blacklisted_devices(
    db: AsyncSession = Depends(get_db), admin: Admin = Depends(get_current_admin)
):
    result = await db.execute(select(BlacklistedHardware))
    return {"blacklisted_devices": result.scalars().all()}


@router.delete("/security/blacklist/{hardware_id}")
async def unblock_device(
    hardware_id: str,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    query = await db.execute(
        select(BlacklistedHardware).where(
            BlacklistedHardware.hardware_id == hardware_id
        )
    )
    item = query.scalars().first()
    if item:
        await db.delete(item)
    device_query = await db.execute(
        select(Device).where(Device.hardware_id == hardware_id)
    )
    for d in device_query.scalars().all():
        d.is_blocked = False
    await db.commit()
    return {"status": "success"}


@router.put("/devices/{device_id}/block")
async def toggle_device_block(
    device_id: int,
    request: BlockDeviceRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    query = await db.execute(
        select(Device).options(selectinload(Device.user)).where(Device.id == device_id)
    )
    device = query.scalars().first()
    if not device:
        raise AppErrors.DEVICE_NOT_FOUND
    device.is_blocked = request.is_blocked
    hw_id = device.hardware_id
    bl_query = await db.execute(
        select(BlacklistedHardware).where(BlacklistedHardware.hardware_id == hw_id)
    )
    bl_entry = bl_query.scalars().first()
    if request.is_blocked:
        if not bl_entry:
            db.add(BlacklistedHardware(hardware_id=hw_id, reason=request.reason))
    else:
        if bl_entry:
            await db.delete(bl_entry)
    action_type = "MANUAL_BLOCK" if request.is_blocked else "MANUAL_UNBLOCK"
    db.add(
        DeviceAuditLog(
            mobile=device.user.mobile if device.user else "Unknown",
            hardware_id=hw_id,
            action=action_type,
            reason=f"Admin: {request.reason}",
        )
    )
    await db.commit()
    return {"status": "success", "is_blocked": device.is_blocked}


@router.post("/security/blacklist/{hardware_id}/unblock")
async def unblock_device_from_blacklist(
    hardware_id: str,
    request: UnblockRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    query = await db.execute(
        select(BlacklistedHardware).where(
            BlacklistedHardware.hardware_id == hardware_id
        )
    )
    item = query.scalars().first()
    if item:
        await db.delete(item)
    device_query = await db.execute(
        select(Device)
        .options(selectinload(Device.user))
        .where(Device.hardware_id == hardware_id)
    )
    mobile_number = "Unknown"
    for d in device_query.scalars().all():
        d.is_blocked = False
        if d.user:
            mobile_number = d.user.mobile
    db.add(
        DeviceAuditLog(
            mobile=mobile_number,
            hardware_id=hardware_id,
            action="MANUAL_UNBLOCK",
            reason=f"Admin: {request.reason}",
        )
    )
    await db.commit()
    return {"status": "success"}


@router.post("/vault/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_upload_vault(
    request: VaultBulkUploadRequest,
    vault_db: AsyncSession = Depends(get_vault_db),
    admin: Admin = Depends(get_current_admin),
):
    for item in request.items:
        new_vault = VaultItem(
            uuid=item.uuid,
            file_hash=item.file_hash,
            decryption_key=f"{item.aes_key}:{item.aes_iv}",
            download_url=f"/downloads/{item.original_filename}"
            if item.original_filename
            else "",
        )
        vault_db.add(new_vault)
    await vault_db.commit()
    return {"status": "success"}
