import logging
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from fastapi import HTTPException, status

from app.models.user import User
from app.models.device import Device
from app.models.security_log import UnauthorizedAttempt
from app.core.security import create_access_token, verify_password
from app.schemas.client.auth import RequestOtpSchema, VerifyRequest


class ClientAuthService:
    @staticmethod
    async def request_otp(
        payload: RequestOtpSchema, ip_address: str, db: AsyncSession
    ) -> dict:
        stmt = select(User).where(
            or_(User.mobile == payload.identifier, User.email == payload.identifier)
        )
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user or not user.is_active:
            return {"status": "success", "message": "OTP sent successfully"}

        otp_code = f"{secrets.randbelow(1000000):06d}"

        user.otp_code = otp_code
        user.otp_expire = datetime.now(timezone.utc) + timedelta(minutes=2)
        await db.commit()

        print(f"\n[SECURITY] OTP for {payload.identifier} is {otp_code}\n")

        return {"status": "success", "message": "OTP sent successfully"}

    @staticmethod
    async def verify_otp(
        payload: VerifyRequest, ip_address: str, db: AsyncSession
    ) -> dict:
        stmt = select(User).where(
            or_(User.mobile == payload.identifier, User.email == payload.identifier)
        )
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User account is blocked"
            )

        is_authenticated = False

        if payload.password:
            user_hash = getattr(user, "hashed_password", None)
            if user_hash and verify_password(payload.password, user_hash):
                is_authenticated = True
        elif payload.code:
            if user.otp_code and payload.code == user.otp_code:
                if user.otp_expire and user.otp_expire < datetime.now(timezone.utc):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED, detail="OTP expired"
                    )
                is_authenticated = True

        if not is_authenticated:
            failed_attempt = UnauthorizedAttempt(
                identifier=payload.identifier,
                hardware_id=payload.hardware_id,
                ip_address=ip_address,
            )
            db.add(failed_attempt)
            await db.commit()

            logging.warning(
                f"Failed auth attempt for {payload.identifier} from IP {ip_address}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        dev_stmt = select(Device).where(
            Device.hardware_id == payload.hardware_id, Device.user_id == user.id
        )
        dev_res = await db.execute(dev_stmt)
        device = dev_res.scalars().first()

        if not device:
            new_device = Device(
                user_id=user.id,
                hardware_id=payload.hardware_id,
                system_specs=payload.system_specs,
            )
            db.add(new_device)
            await db.commit()
        elif device.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This device has been permanently blocked",
            )

        user.otp_code = None
        user.otp_expire = None
        await db.commit()

        access_token = create_access_token(
            data={
                "sub": payload.identifier,
                "role": "client",
                "hid": payload.hardware_id,
            }
        )
        return {"access_token": access_token, "token_type": "bearer"}
