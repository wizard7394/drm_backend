from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List

from app.api.dependencies import get_db, get_current_admin
from app.core.errors import AppErrors
from app.models.admin import Admin
from app.models.course import Course, CourseNode
from app.models.vault import VideoVault
from app.models.device import Device
from app.models.security_log import BlacklistedHardware
from app.models.hardware_reset import HardwareReset  # noqa: F401
from app.models.license import License  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.user import User  # noqa: F401

router = APIRouter()

# --- Schemas ---
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

# --- Security & Device Management ---
@router.get("/devices")
async def get_all_devices(
    db: AsyncSession = Depends(get_db), admin: Admin = Depends(get_current_admin)
):
    result = await db.execute(select(Device))
    return {"devices": result.scalars().all()}

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
        select(BlacklistedHardware).where(BlacklistedHardware.hardware_id == hardware_id)
    )
    item = query.scalars().first()
    if not item:
        raise AppErrors.DEVICE_NOT_FOUND
    await db.delete(item)
    await db.commit()
    return {"status": "success", "message": f"Device {hardware_id} unblocked"}

# --- Course & Node Management ---
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
        v_q = await db.execute(select(VideoVault).where(VideoVault.id == request.vault_id))
        v_item = v_q.scalars().first()
        if v_item: v_item.status = "used"

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
            title=item.original_filename.split("/")[-1] if item.original_filename else "Untitled",
            vault_id=item.id,
        )
        db.add(new_video)
        item.status = "used"

    await db.commit()
    return {"status": "success", "processed_items": len(vault_items)}