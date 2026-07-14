from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import AuthService

from app.core.database import get_db

router = APIRouter()


@router.post("/login")
async def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    return await AuthService.admin_login(form_data, db)
