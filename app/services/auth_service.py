import secrets
import bcrypt
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.admin import Admin
from app.models.device import Device
from app.schemas.auth import LoginRequest, VerifyRequest
from app.core.security import create_access_token
from app.core.errors import AppErrors


class AuthService:
    @staticmethod
    async def request_otp(payload: LoginRequest, db: AsyncSession):
        user_query = await db.execute(select(User).where(User.mobile == payload.mobile))
        user = user_query.scalars().first()

        if not user or not user.is_active:
            raise AppErrors.USER_NOT_FOUND

        secure_otp = "".join(str(secrets.randbelow(10)) for _ in range(6))

        user.otp_code = secure_otp
        user.otp_expire = datetime.now(timezone.utc) + timedelta(minutes=2)

        await db.commit()

        print(f"\n[SECURITY] OTP for {payload.mobile}: {secure_otp}\n")

        return {"status": "success", "message": "verification_code_sent"}

    @staticmethod
    async def verify_otp(payload: VerifyRequest, db: AsyncSession):
        user_query = await db.execute(select(User).where(User.mobile == payload.mobile))
        user = user_query.scalars().first()

        if not user or not user.is_active:
            raise AppErrors.USER_NOT_FOUND

        if not user.otp_code or user.otp_code != payload.code:
            raise AppErrors.INVALID_OTP

        expire_time = user.otp_expire
        if expire_time and expire_time.tzinfo is None:
            expire_time = expire_time.replace(tzinfo=timezone.utc)

        if not expire_time or datetime.now(timezone.utc) > expire_time:
            raise AppErrors.OTP_EXPIRED

        user.otp_code = None
        user.otp_expire = None

        device_query = await db.execute(select(Device).where(Device.user_id == user.id))
        user_devices = device_query.scalars().all()

        current_device = None
        if not user_devices:
            current_device = Device(
                user_id=user.id,
                hardware_id=payload.hardware_id,
            )
            db.add(current_device)
            await db.flush()
        else:
            for d in user_devices:
                if d.hardware_id == payload.hardware_id:
                    current_device = d
                    break

            if not current_device:
                raise AppErrors.HARDWARE_MISMATCH

        if current_device.is_blocked:
            raise AppErrors.DEVICE_BLOCKED

        current_device.last_login = datetime.now(timezone.utc)
        await db.commit()

        access_token = create_access_token(
            data={"sub": user.mobile, "hid": current_device.hardware_id}
        )

        return {
            "status": "success",
            "access_token": access_token,
            "message": "authentication_successful",
        }

    @staticmethod
    async def admin_login(form_data, db: AsyncSession):
        admin_query = await db.execute(
            select(Admin).where(Admin.username == form_data.username)
        )
        admin_user = admin_query.scalars().first()

        if not admin_user:
            raise AppErrors.INVALID_CREDENTIALS

        is_password_correct = bcrypt.checkpw(
            form_data.password.encode("utf-8"),
            admin_user.hashed_password.encode("utf-8"),
        )

        if not is_password_correct:
            raise AppErrors.INVALID_CREDENTIALS

        if not admin_user.is_active:
            raise AppErrors.ADMIN_DISABLED

        access_token = create_access_token(
            data={"sub": admin_user.username, "role": "super_admin"}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "status": "success",
            "message": "admin_authentication_successful",
        }
