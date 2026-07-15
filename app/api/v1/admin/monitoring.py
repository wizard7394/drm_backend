from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.v1.admin.dependencies import get_current_admin
from app.models.admin import Admin
from app.services.monitoring_service import MonitoringService
from app.schemas.monitoring import (
    UserMonitoringResponse,
    BlockDeviceRequest,
    ResetHardwareRequest,
)

router = APIRouter()


@router.get("/user/{identifier}/devices", response_model=UserMonitoringResponse)
async def get_user_devices_info(
    identifier: str,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await MonitoringService.get_user_devices(identifier, db)


@router.post("/device/block")
async def block_user_device(
    payload: BlockDeviceRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await MonitoringService.block_device(payload, db)


@router.post("/device/reset")
async def reset_user_hardware(
    payload: ResetHardwareRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await MonitoringService.reset_hardware(payload, current_admin.id, db)
