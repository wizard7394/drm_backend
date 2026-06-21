import secrets
import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user import User
from app.models.admin import Admin
from app.models.device import Device
from app.models.hardware_reset import HardwareReset  # noqa: F401
from app.models.license import License  # noqa: F401
from app.models.security_log import UnauthorizedAttempt, BlacklistedHardware

from app.schemas.auth import RequestOtpSchema, VerifyRequest
from app.core.security import create_access_token
from app.core.errors import AppErrors


# Helper to generate timezone-naive UTC datetime for asyncpg compatibility
def get_naive_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuthService:
    @staticmethod
    async def request_otp(payload: RequestOtpSchema, ip_address: str, db: AsyncSession):
        now = get_naive_utc_now()
        hardware_id = payload.hardware_id

        blacklisted_query = await db.execute(
            select(BlacklistedHardware).where(
                BlacklistedHardware.hardware_id == hardware_id
            )
        )
        if blacklisted_query.scalars().first():
            raise AppErrors.DEVICE_BLOCKED

        device_query = await db.execute(
            select(Device).where(Device.hardware_id == hardware_id)
        )
        existing_device = device_query.scalars().first()
        if existing_device and existing_device.is_blocked:
            raise AppErrors.DEVICE_BLOCKED

        one_hour_ago = now - timedelta(hours=1)
        ip_count_query = await db.execute(
            select(func.count(UnauthorizedAttempt.id))
            .where(UnauthorizedAttempt.ip_address == ip_address)
            .where(UnauthorizedAttempt.attempted_at >= one_hour_ago)
        )
        ip_attempts = ip_count_query.scalar() or 0

        if ip_attempts >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="IP_RATE_LIMITED"
            )

        user_query = await db.execute(select(User).where(User.mobile == payload.mobile))
        user = user_query.scalars().first()

        if not user or not user.is_active:
            attempt = UnauthorizedAttempt(
                mobile=payload.mobile,
                hardware_id=hardware_id,
                ip_address=ip_address,
                attempted_at=now,
            )
            db.add(attempt)
            await db.flush()

            hw_count_query = await db.execute(
                select(func.count(UnauthorizedAttempt.id)).where(
                    UnauthorizedAttempt.hardware_id == hardware_id
                )
            )
            hw_attempts = hw_count_query.scalar() or 0

            if hw_attempts >= 3:
                blacklist_entry = BlacklistedHardware(
                    hardware_id=hardware_id,
                    reason="Too many unauthorized login attempts",
                )
                db.add(blacklist_entry)

            await db.commit()
            raise AppErrors.USER_NOT_FOUND

        secure_otp = "".join(str(secrets.randbelow(10)) for _ in range(6))

        user.otp_code = secure_otp
        user.otp_expire = now + timedelta(minutes=2)

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

        now_naive = get_naive_utc_now()
        expire_time = user.otp_expire

        # Neutralize any timezone info if present in the database record
        if expire_time and expire_time.tzinfo is not None:
            expire_time = expire_time.replace(tzinfo=None)

        if not expire_time or now_naive > expire_time:
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
                system_specs=payload.system_specs,
            )
            db.add(current_device)
            await db.flush()
        else:
            for d in user_devices:
                if d.hardware_id == payload.hardware_id:
                    current_device = d
                    current_device.system_specs = payload.system_specs
                    break

            if not current_device:
                raise AppErrors.HARDWARE_MISMATCH

        if current_device.is_blocked:
            raise AppErrors.DEVICE_BLOCKED

        current_device.last_login = now_naive
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
