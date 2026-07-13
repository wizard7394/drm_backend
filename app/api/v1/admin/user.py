from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.admin import Admin
from app.models.license import License
from app.models.user import User
from app.models.device import Device
from app.models.transaction import Transaction
from app.models.security_log import DeviceAuditLog
from app.models.course import Course, WatchedVideo

from app.core.database import get_db, get_vault_db
from app.api.v1.admin.dependencies import get_current_admin

router = APIRouter()


class UserCreateRequest(BaseModel):
    mobile: str
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/list")
async def get_all_users(
    db: AsyncSession = Depends(get_db), admin: Admin = Depends(get_current_admin)
):
    result = await db.execute(select(User).order_by(desc(User.id)))
    users = result.scalars().all()

    return {
        "users": [
            {
                "id": u.id,
                "mobile": u.mobile,
                "name": f"{u.first_name or ''} {u.last_name or ''}".strip()
                or "UNKNOWN",
                "email": u.email or "NO EMAIL",
                "is_active": u.is_active,
            }
            for u in users
        ]
    }


@router.post("/create")
async def create_new_user(
    payload: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    existing_query = await db.execute(select(User).where(User.mobile == payload.mobile))
    if existing_query.scalars().first():
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(mobile=payload.mobile, is_active=payload.is_active)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {"status": "success", "user_id": new_user.id}


@router.put("/{user_id}/update")
async def update_user_profile(
    user_id: int,
    payload: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    query = await db.execute(select(User).where(User.id == user_id))
    user = query.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.first_name is not None:
        user.first_name = payload.first_name
    if payload.last_name is not None:
        user.last_name = payload.last_name
    if payload.email is not None:
        user.email = payload.email
    if payload.is_active is not None:
        user.is_active = payload.is_active

    await db.commit()
    return {"status": "success"}


@router.get("/{user_id}/profile")
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    query = await db.execute(select(User).where(User.id == user_id))
    user = query.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "mobile": user.mobile,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "violation_count": user.violation_count,
        "is_active": user.is_active,
    }


@router.get("/{user_id}/devices")
async def get_user_devices(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    query = await db.execute(select(Device).where(Device.user_id == user_id))
    devices = query.scalars().all()

    return {
        "devices": [
            {
                "id": d.id,
                "hardware_id": d.hardware_id,
                "system_specs": d.system_specs,
                "is_blocked": d.is_blocked,
                "last_login": d.last_login,
            }
            for d in devices
        ]
    }


@router.get("/{user_id}/heatmap")
async def get_user_heatmap(
    user_id: int,
    vault_db: AsyncSession = Depends(get_vault_db),
    admin: Admin = Depends(get_current_admin),
):
    query = await vault_db.execute(
        select(WatchedVideo).where(WatchedVideo.user_id == user_id)
    )
    watched_logs = query.scalars().all()

    return {
        "heatmap": [
            {"vault_uuid": w.vault_uuid, "watched_at": w.watched_at}
            for w in watched_logs
        ]
    }


@router.get("/{user_id}/transactions")
async def get_user_transactions(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    query = await db.execute(select(Transaction).where(Transaction.user_id == user_id))
    transactions = query.scalars().all()

    return {
        "transactions": [
            {
                "id": t.id,
                "amount": getattr(t, "amount", 0),
                "status": getattr(t, "status", "unknown"),
            }
            for t in transactions
        ]
    }


@router.get("/{user_id}/logs")
async def get_user_logs(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    user_query = await db.execute(select(User).where(User.id == user_id))
    user = user_query.scalars().first()

    if not user:
        return {"logs": []}

    logs_query = await db.execute(
        select(DeviceAuditLog).where(DeviceAuditLog.mobile == user.mobile)
    )
    logs = logs_query.scalars().all()

    return {
        "logs": [
            {"id": log.id, "action": log.action, "reason": log.reason} for log in logs
        ]
    }


@router.get("/{user_id}/courses")
async def get_user_courses_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    vault_db: AsyncSession = Depends(get_vault_db),
    admin: Admin = Depends(get_current_admin),
):
    stmt = select(License.course_id).where(
        License.user_id == user_id, License.is_active
    )
    result = await db.execute(stmt)
    course_ids = result.scalars().all()

    if not course_ids:
        return {"courses": []}

    course_stmt = select(Course).where(Course.id.in_(course_ids))
    course_res = await vault_db.execute(course_stmt)
    courses = course_res.scalars().all()

    return {"courses": [{"id": c.id, "title": c.title} for c in courses]}
