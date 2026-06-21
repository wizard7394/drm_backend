from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import selectinload
from app.api.dependencies import get_db, get_current_admin
from app.core.errors import AppErrors
from app.models.admin import Admin
from app.models.course import Course, CourseNode
from app.models.vault import VideoVault
from app.models.device import Device
from app.models.security_log import BlacklistedHardware, DeviceAuditLog
from app.models.hardware_reset import HardwareReset  # noqa: F401
from app.models.license import License  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.user import User

router = APIRouter()


class AutoBuildRequest(BaseModel):
    batch_name: str


class CreateCourseRequest(BaseModel):
    title: str
    watermark_text: Optional[str] = None
    watermark_color: Optional[str] = None


class CreateNodeRequest(BaseModel):
    course_id: int
    parent_id: Optional[int] = None
    item_type: str
    title: str
    sort_order: int = 1
    video_url: Optional[str] = None
    duration: Optional[int] = None
    attachment_url: Optional[str] = None
    vault_id: Optional[int] = None


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
    db: AsyncSession = Depends(get_db), admin: Admin = Depends(get_current_admin)
):
    users_count = await db.execute(select(func.count(User.id)))
    courses_count = await db.execute(select(func.count(Course.id)))
    devices_count = await db.execute(select(func.count(Device.id)))

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
    devices = device_query.scalars().all()
    for d in devices:
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
    audit_log = DeviceAuditLog(
        mobile=device.user.mobile if device.user else "Unknown",
        hardware_id=hw_id,
        action=action_type,
        reason=f"Admin: {request.reason}",
    )
    db.add(audit_log)

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
    devices = device_query.scalars().all()
    mobile_number = "Unknown"

    for d in devices:
        d.is_blocked = False
        if d.user:
            mobile_number = d.user.mobile

    audit_log = DeviceAuditLog(
        mobile=mobile_number,
        hardware_id=hardware_id,
        action="MANUAL_UNBLOCK",
        reason=f"Admin: {request.reason}",
    )
    db.add(audit_log)

    await db.commit()
    return {"status": "success"}


@router.get("/courses")
async def get_all_courses(
    db: AsyncSession = Depends(get_db), admin: Admin = Depends(get_current_admin)
):
    query = await db.execute(select(Course).order_by(Course.id.desc()))
    courses = query.scalars().all()
    result = []
    for course in courses:
        result.append(
            {
                "id": course.id,
                "title": course.title,
                "watermark_text": course.watermark_text,
                "is_active": course.is_active,
            }
        )
    return {"status": "success", "courses": result}


@router.post("/course", status_code=status.HTTP_201_CREATED)
async def create_course(
    request: CreateCourseRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    new_course = Course(
        title=request.title,
        watermark_text=request.watermark_text,
        watermark_color=request.watermark_color,
    )
    db.add(new_course)
    await db.commit()
    return {"status": "success", "course_id": new_course.id}


@router.delete("/course/{course_id}")
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    query = await db.execute(select(Course).where(Course.id == course_id))
    course = query.scalars().first()
    if not course:
        raise AppErrors.COURSE_NOT_FOUND
    await db.delete(course)
    await db.commit()
    return {"status": "success"}


@router.post("/node", status_code=status.HTTP_201_CREATED)
async def create_node(
    request: CreateNodeRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    if request.vault_id:
        v_q = await db.execute(
            select(VideoVault).where(VideoVault.id == request.vault_id)
        )
        v_item = v_q.scalars().first()
        if v_item:
            v_item.status = "used"

    new_node = CourseNode(
        course_id=request.course_id,
        parent_id=request.parent_id,
        item_type=request.item_type,
        title=request.title,
        sort_order=request.sort_order,
        video_url=request.video_url,
        duration=request.duration,
        attachment_url=request.attachment_url,
        vault_id=request.vault_id,
    )
    db.add(new_node)
    await db.commit()
    return {"status": "success"}


@router.post("/vault/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_upload_vault(
    request: VaultBulkUploadRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    for item in request.items:
        new_vault = VideoVault(
            course_id=request.course_id,
            batch_name=request.batch_name,
            uuid=item.uuid,
            original_filename=item.original_filename,
            file_hash=item.file_hash,
            aes_key=item.aes_key,
            aes_iv=item.aes_iv,
            status="unused",
        )
        db.add(new_vault)
    await db.commit()
    return {"status": "success"}


@router.post("/vault/{course_id}/auto-build")
async def auto_build_course_tree(
    course_id: int,
    request: AutoBuildRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    query = await db.execute(
        select(VideoVault).where(
            VideoVault.course_id == course_id,
            VideoVault.batch_name == request.batch_name,
            VideoVault.status == "unused",
        )
    )
    vault_items = query.scalars().all()
    if not vault_items:
        raise AppErrors.NO_UNUSED_VAULT_ITEMS

    for item in vault_items:
        new_video = CourseNode(
            course_id=course_id,
            item_type="video",
            title=item.original_filename.split("/")[-1]
            if item.original_filename
            else "Untitled",
            vault_id=item.id,
        )
        db.add(new_video)
        item.status = "used"

    await db.commit()
    return {"status": "success"}
