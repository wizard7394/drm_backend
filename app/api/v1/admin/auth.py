from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.admin.auth_service import AuthService
from app.core.database import get_db

router = APIRouter()


@router.post("/login")
async def admin_login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    ip_address = request.client.host
    return await AuthService.admin_login(form_data, ip_address, db)
