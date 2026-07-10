from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import ALGORITHM, SECRET_KEY
from app.core.database import get_db, get_vault_db  # noqa: F401
from app.models.user import User
from app.models.admin import Admin
from app.models.device import Device
from app.models.hardware_reset import HardwareReset  # noqa: F401
from app.models.license import License  # noqa: F401
from app.models.security_log import UnauthorizedAttempt, BlacklistedHardware  # noqa: F401
from app.core.errors import AppErrors

admin_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/auth/login")
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

    if hardware_id:
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


async def get_current_admin(
    token: str = Depends(admin_oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")

        if username is None or role != "super_admin":
            raise AppErrors.INSUFFICIENT_PERMISSIONS

    except jwt.ExpiredSignatureError:
        raise AppErrors.TOKEN_EXPIRED
    except JWTError:
        raise AppErrors.INVALID_TOKEN

    result = await db.execute(select(Admin).where(Admin.username == username))
    admin = result.scalars().first()

    if admin is None or not admin.is_active:
        raise AppErrors.ADMIN_NOT_FOUND

    return admin
