import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.admin import Admin
from app.core.security import verify_password, create_access_token

DUMMY_HASH = "$2b$12$ThisIsADummyHashForTimingAttackMitigationPurposeOnly"


class AdminAuthService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate_admin(self, username: str, password: str, ip_address: str) -> dict:
        admin = self.db.query(Admin).filter(Admin.username == username).first()

        if not admin:
            verify_password(password, DUMMY_HASH)
            logging.warning(f"Failed admin login attempt from IP {ip_address}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        if not verify_password(password, admin.hashed_password):
            logging.warning(
                f"Failed admin login attempt for user {username} from IP {ip_address}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        if not admin.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin account is disabled",
            )

        access_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})
        return {"access_token": access_token, "token_type": "bearer"}
