from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_vault_db
from app.api.v1.admin.dependencies import get_current_admin
from app.models.admin import Admin
from app.services.admin.user_service import AdminUserService

from app.schemas.admin.user import (
    UserCreateAdmin,
    UserDevicesResponse,
    UserLogsResponse,
    UserUpdateAdmin,
    UserListResponse,
    AdminUserProfileResponse,
    UserHeatmapResponse,
    UserTransactionsResponse,
    UserCoursesResponse,
)

router = APIRouter()


@router.get("/list", response_model=UserListResponse)
async def get_all_users(
    db: AsyncSession = Depends(get_db), admin: Admin = Depends(get_current_admin)
):
    return await AdminUserService.get_all_users(db)


@router.post("/create")
async def create_new_user(
    payload: UserCreateAdmin,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    return await AdminUserService.create_user(payload, db)


@router.put("/{user_id}/update")
async def update_user_profile(
    user_id: int,
    payload: UserUpdateAdmin,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    return await AdminUserService.update_user(user_id, payload, db)


@router.get("/{user_id}/profile", response_model=AdminUserProfileResponse)
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    return await AdminUserService.get_user_profile(user_id, db)


@router.get("/{user_id}/heatmap", response_model=UserHeatmapResponse)
async def get_user_heatmap(
    user_id: int,
    vault_db: AsyncSession = Depends(get_vault_db),
    admin: Admin = Depends(get_current_admin),
):
    return await AdminUserService.get_user_heatmap(user_id, vault_db)


@router.get("/{user_id}/devices", response_model=UserDevicesResponse)
async def get_user_devices(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    return await AdminUserService.get_user_devices(user_id, db)


@router.get("/{user_id}/logs", response_model=UserLogsResponse)
async def get_user_logs(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    return await AdminUserService.get_user_logs(user_id, db)


@router.get("/{user_id}/transactions", response_model=UserTransactionsResponse)
async def get_user_transactions(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    return await AdminUserService.get_user_transactions(user_id, db)


@router.get("/{user_id}/courses", response_model=UserCoursesResponse)
async def get_user_courses_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    vault_db: AsyncSession = Depends(get_vault_db),
    admin: Admin = Depends(get_current_admin),
):
    return await AdminUserService.get_user_courses(user_id, db, vault_db)
