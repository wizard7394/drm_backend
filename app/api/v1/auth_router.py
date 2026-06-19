from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import RequestOtpSchema, VerifyRequest

router = APIRouter()


@router.post("/request-otp")
async def request_otp(
    payload: RequestOtpSchema, request: Request, db: AsyncSession = Depends(get_db)
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    return await AuthService.request_otp(payload, client_ip, db)


@router.post("/verify-otp")
async def verify_otp(payload: VerifyRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.verify_otp(payload, db)


@router.post("/admin/login")
async def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    return await AuthService.admin_login(form_data, db)
