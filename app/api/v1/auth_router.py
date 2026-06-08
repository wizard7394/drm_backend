from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import secrets
from datetime import datetime, timedelta, timezone

from app.api.dependencies import get_db
from app.schemas.auth import HardwareAuthRequest, AuthResponse, SignedAuthResponse
from app.services.auth_service import verify_and_register_device
from app.core.security import sign_payload, create_access_token
from app.models.user import User

router = APIRouter()

class OTPRequest(BaseModel):
    phone_number: str

@router.post("/hardware", response_model=SignedAuthResponse)
async def validate_hardware(
    request: HardwareAuthRequest, db: AsyncSession = Depends(get_db)
):
    token = await verify_and_register_device(request, db)
    
    response_payload = AuthResponse(
        status="success", 
        access_token=token, 
        message="Device processed successfully."
    )

    digital_signature = sign_payload(response_payload)

    return SignedAuthResponse(
        payload=response_payload, 
        signature=digital_signature
    )

@router.post("/request-otp")
async def request_otp(payload: OTPRequest, db: AsyncSession = Depends(get_db)):
    phone = payload.phone_number
    
    user_query = await db.execute(select(User).where(User.phone_number == phone))
    user = user_query.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=404, 
            detail="No purchased courses found for this account. Please visit the website to purchase."
        )
        
    secure_otp = "".join(str(secrets.randbelow(10)) for _ in range(7))
    
    user.otp_code = secure_otp
    user.otp_expire = datetime.now(timezone.utc) + timedelta(minutes=2)
    
    await db.commit()
    
    print(f"\nSECURITY ALERT - OTP for {phone}: {secure_otp}\n")
    
    return {"status": "success", "message": "Verification code generated successfully."}


class VerifyOTPRequest(BaseModel):
    phone_number: str
    code: str

@router.post("/verify-otp")
async def verify_otp(payload: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    user_query = await db.execute(select(User).where(User.phone_number == payload.phone_number))
    user = user_query.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found in system.")

    if not user.otp_code or user.otp_code != payload.code:
        raise HTTPException(status_code=401, detail="Invalid verification code.")

    expire_time = user.otp_expire
    if expire_time and expire_time.tzinfo is None:
        expire_time = expire_time.replace(tzinfo=timezone.utc)

    if not expire_time or datetime.now(timezone.utc) > expire_time:
        raise HTTPException(status_code=401, detail="Verification code has expired.")

    user.otp_code = None
    user.otp_expire = None
    user.last_active = datetime.now(timezone.utc)
    await db.commit()

    access_token = create_access_token(data={"sub": str(user.id), "phone": user.phone_number})

    return {
        "status": "success",
        "access_token": access_token,
        "message": "Authentication successful."
    }