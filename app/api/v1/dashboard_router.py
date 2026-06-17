from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user, get_current_admin
from app.models.user import User
from app.models.admin import Admin
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/admin/stats", status_code=status.HTTP_200_OK)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    stats = await DashboardService.get_admin_stats(db)
    return {"status": "success", "stats": stats}


@router.get("/my-courses", status_code=status.HTTP_200_OK)
async def get_my_courses(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return await DashboardService.get_user_courses(current_user, db)
