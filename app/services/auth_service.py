import secrets
import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.core.security import create_access_token, create_admin_access_token

from app.models.user import User
from app.models.admin import Admin
from app.models.device import Device
from app.models.hardware_reset import HardwareReset  # noqa: F401
from app.models.license import License  # noqa: F401
from app.models.security_log import (
    UnauthorizedAttempt,
    BlacklistedHardware,
    DeviceAuditLog,
)

from app.schemas.auth import RequestOtpSchema, VerifyRequest
from app.core.errors import AppErrors


def get_naive_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuthService:
    @staticmethod
    async def request_otp(payload: RequestOtpSchema, ip_address: str, db: AsyncSession):
        now = get_naive_utc_now()
        hardware_id = payload.hardware_id
        identifier = payload.identifier

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

        user_query = await db.execute(
            select(User).where(or_(User.mobile == identifier, User.email == identifier))
        )
        user = user_query.scalars().first()

        if not user or not user.is_active:
            attempt = UnauthorizedAttempt(
                mobile=identifier,
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

        print(f"\n[SECURITY] OTP for {identifier}: {secure_otp}\n")

        return {"status": "success", "message": "verification_code_sent"}

    @staticmethod
    async def verify_otp(payload: VerifyRequest, ip_address: str, db: AsyncSession):
        now_naive = get_naive_utc_now()
        one_hour_ago = now_naive - timedelta(hours=1)

        ip_count_query = await db.execute(
            select(func.count(UnauthorizedAttempt.id))
            .where(UnauthorizedAttempt.ip_address == ip_address)
            .where(UnauthorizedAttempt.attempted_at >= one_hour_ago)
        )
        if (ip_count_query.scalar() or 0) >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="IP_RATE_LIMITED"
            )

        identifier = payload.identifier
        user_query = await db.execute(
            select(User).where(or_(User.mobile == identifier, User.email == identifier))
        )
        user = user_query.scalars().first()

        if not user or not user.is_active:
            raise AppErrors.USER_NOT_FOUND

        async def register_failed_attempt():
            attempt = UnauthorizedAttempt(
                mobile=identifier,
                hardware_id=payload.hardware_id,
                ip_address=ip_address,
                attempted_at=now_naive,
            )
            db.add(attempt)
            await db.commit()

        if not user.otp_code or user.otp_code != payload.code:
            await register_failed_attempt()
            raise AppErrors.INVALID_OTP

        expire_time = user.otp_expire
        if expire_time and expire_time.tzinfo is not None:
            expire_time = expire_time.replace(tzinfo=None)

        if not expire_time or now_naive > expire_time:
            await register_failed_attempt()
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
                for existing_d in user_devices:
                    existing_d.is_blocked = True

                    audit_log = DeviceAuditLog(
                        mobile=user.mobile,
                        hardware_id=existing_d.hardware_id,
                        action="AUTO_BLOCK_MISMATCH",
                        reason=f"System auto-blocked due to unauthorized login attempt from new hardware ID: {payload.hardware_id}",
                    )
                    db.add(audit_log)

                await db.commit()
                raise AppErrors.HARDWARE_MISMATCH

        if current_device.is_blocked:
            raise AppErrors.DEVICE_BLOCKED

        current_device.last_login = now_naive
        await db.commit()

        primary_identifier = user.mobile or user.email or identifier
        access_token = create_access_token(
            data={"sub": primary_identifier, "hid": current_device.hardware_id}
        )

        return {
            "status": "success",
            "access_token": access_token,
            "message": "authentication_successful",
        }

    @staticmethod
    async def admin_login(form_data, ip_address: str, db: AsyncSession):
        now = get_naive_utc_now()
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

        admin_query = await db.execute(
            select(Admin).where(Admin.username == form_data.username)
        )
        admin_user = admin_query.scalars().first()

        dummy_hash = b"$2b$12$vqO6gXn9L0oZ5z2K2o5sYuqO6gXn9L0oZ5z2K2o5sYuqO6gXn9L0o"
        is_password_correct = False

        if admin_user:
            is_password_correct = bcrypt.checkpw(
                form_data.password.encode("utf-8"),
                admin_user.hashed_password.encode("utf-8"),
            )
        else:
            bcrypt.checkpw(
                form_data.password.encode("utf-8"),
                dummy_hash,
            )

        if not admin_user or not is_password_correct:
            attempt = UnauthorizedAttempt(
                mobile=form_data.username,
                hardware_id="ADMIN_LOGIN_ATTEMPT",
                ip_address=ip_address,
                attempted_at=now,
            )
            db.add(attempt)
            await db.commit()
            raise AppErrors.INVALID_CREDENTIALS

        if not admin_user.is_active:
            raise AppErrors.ADMIN_DISABLED

        access_token = create_admin_access_token(
            data={"sub": admin_user.username, "role": "super_admin"}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "status": "success",
            "message": "admin_authentication_successful",
        }
