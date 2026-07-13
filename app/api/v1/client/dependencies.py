from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import ALGORITHM, SECRET_KEY
from app.core.database import get_db
from app.models.user import User
from app.models.device import Device
from app.core.errors import AppErrors

client_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/client/auth/verify-otp")


async def get_current_user(
    token: str = Depends(client_oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        mobile: str = payload.get("sub")
        hardware_id: str = payload.get("hid")

        if mobile is None:
            raise AppErrors.CREDENTIALS_EXCEPTION

    except jwt.ExpiredSignatureError:
        raise AppErrors.TOKEN_EXPIRED
    except JWTError:
        raise AppErrors.INVALID_TOKEN

    result = await db.execute(select(User).where(User.mobile == mobile))
    user = result.scalars().first()

    if user is None or not user.is_active:
        raise AppErrors.USER_NOT_FOUND

    if not hardware_id:
        raise AppErrors.HARDWARE_MISMATCH

    dev_result = await db.execute(
        select(Device).where(
            Device.user_id == user.id, Device.hardware_id == hardware_id
        )
    )
    device = dev_result.scalars().first()

    if device is None:
        raise AppErrors.HARDWARE_MISMATCH
    if device.is_blocked:
        raise AppErrors.DEVICE_BLOCKED

    return user
