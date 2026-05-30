from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.device import HardwareDevice

security = HTTPBearer()
SECRET_KEY = "DJHNIUY#@HDF&^*HFVJKDSfhyuewfbnjhdvnc78#NVC*#Bnfv8wnv"
ALGORITHM = "HS256"

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_device(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        device_hash = payload.get("device_hash")
        license_id = payload.get("license_id")

        if device_hash is None or license_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials.")

    device_query = await db.execute(select(HardwareDevice).where(
        HardwareDevice.hardware_hash == device_hash,
        HardwareDevice.license_id == license_id
    ))
    device = device_query.scalars().first()

    if not device:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Device not found.")
    
    if device.is_revoked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device access revoked.")

    return device