from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_vault_db
from app.api.v1.admin.dependencies import get_current_admin
from app.models.admin import Admin
from app.schemas.admin.dashboard import DashboardStatsResponse
from app.services.admin.dashboard_service import AdminDashboardService

router = APIRouter()


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await AdminDashboardService.get_stats(db, vault_db)
