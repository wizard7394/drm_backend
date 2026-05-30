from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db
from app.schemas.auth import HardwareAuthRequest, AuthResponse, SignedAuthResponse
from app.services.auth_service import verify_and_register_device
from app.core.security import sign_payload

router = APIRouter()

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