from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.device import Device
from app.core.errors import AppErrors

client_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/client/auth/verify-otp")


async def get_current_user(
    token: str = Depends(client_oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        identifier: str = payload.get("sub")
        hardware_id: str = payload.get("hid")

        if not identifier or not hardware_id:
            raise AppErrors.INVALID_TOKEN

    except jwt.ExpiredSignatureError:
        raise AppErrors.TOKEN_EXPIRED
    except JWTError:
        raise AppErrors.INVALID_TOKEN

    user_query = await db.execute(
        select(User).where(
            or_(User.mobile == identifier, User.email == identifier), User.is_active
        )
    )
    user = user_query.scalars().first()

    if not user:
        raise AppErrors.USER_NOT_FOUND

    device_query = await db.execute(
        select(Device).where(
            Device.user_id == user.id, Device.hardware_id == hardware_id
        )
    )
    device = device_query.scalars().first()

    if not device:
        raise AppErrors.HARDWARE_MISMATCH

    if device.is_blocked:
        raise AppErrors.DEVICE_BLOCKED

    return user
