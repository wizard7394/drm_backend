from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.auth import LoginRequest, VerifyRequest
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/request-otp")
async def request_otp(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.request_otp(payload, db)


@router.post("/verify-otp")
async def verify_otp(payload: VerifyRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.verify_otp(payload, db)


@router.post("/admin/login")
async def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    return await AuthService.admin_login(form_data, db)
