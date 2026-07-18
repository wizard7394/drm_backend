from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.client.auth_service import ClientAuthService
from app.schemas.client.auth import RequestOtpSchema, VerifyRequest

from app.core.database import get_db

router = APIRouter()


@router.post("/request-otp")
async def request_otp(
    payload: RequestOtpSchema, request: Request, db: AsyncSession = Depends(get_db)
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    return await ClientAuthService.request_otp(payload, client_ip, db)


@router.post("/verify-otp")
async def verify_otp(
    payload: VerifyRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    return await ClientAuthService.verify_otp(payload, client_ip, db)
