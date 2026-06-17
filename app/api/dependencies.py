from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.security import ALGORITHM, SECRET_KEY
from app.core.database import get_db
from app.models.user import User
from app.models.admin import Admin
from app.models.device import Device
from app.core.errors import AppErrors

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
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

    user = db.query(User).filter(User.mobile == mobile).first()
    if user is None or not user.is_active:
        raise AppErrors.USER_NOT_FOUND

    if hardware_id:
        device = (
            db.query(Device)
            .filter(Device.user_id == user.id, Device.hardware_id == hardware_id)
            .first()
        )

        if device is None:
            raise AppErrors.HARDWARE_MISMATCH
        if device.is_blocked:
            raise AppErrors.DEVICE_BLOCKED

    return user


def get_current_admin(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
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

    admin = db.query(Admin).filter(Admin.username == username).first()
    if admin is None or not admin.is_active:
        raise AppErrors.ADMIN_NOT_FOUND

    return admin
