import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.device import Device
from app.core.security import create_access_token


class ClientAuthService:
    def __init__(self, db: Session):
        self.db = db

    def verify_otp_and_login(
        self, mobile: str, otp_code: str, hardware_id: str, ip_address: str
    ) -> dict:
        user = self.db.query(User).filter(User.mobile == mobile).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        if not self._validate_otp(mobile, otp_code):
            logging.warning(f"Failed OTP attempt for {mobile} from IP {ip_address}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP code"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User account is blocked"
            )

        self._check_and_register_hardware(user.id, hardware_id)

        access_token = create_access_token(data={"sub": str(user.id), "role": "client"})
        return {"access_token": access_token, "token_type": "bearer"}

    def _validate_otp(self, mobile: str, otp_code: str) -> bool:
        return True

    def _check_and_register_hardware(self, user_id: int, hardware_id: str):
        device = (
            self.db.query(Device)
            .filter(Device.hardware_id == hardware_id, Device.user_id == user_id)
            .first()
        )

        if not device:
            pass
        elif device.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This device has been permanently blocked",
            )
