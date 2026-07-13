from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import ALGORITHM, SECRET_KEY
from app.core.database import get_db
from app.models.admin import Admin
from app.core.errors import AppErrors

admin_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/auth/login")


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
