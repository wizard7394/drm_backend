import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.models.admin import Admin
from app.core.security import verify_password, create_admin_access_token

DUMMY_HASH = "$2b$12$ThisIsADummyHashForTimingAttackMitigationPurposeOnly"


class AdminAuthService:
    @staticmethod
    async def admin_login(
        form_data: OAuth2PasswordRequestForm, ip_address: str, db: AsyncSession
    ) -> dict:
        result = await db.execute(
            select(Admin).where(Admin.username == form_data.username)
        )
        admin = result.scalars().first()

        if not admin:
            verify_password(form_data.password, DUMMY_HASH)
            logging.warning(f"Failed admin login attempt from IP {ip_address}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        if not verify_password(form_data.password, admin.hashed_password):
            logging.warning(
                f"Failed admin login attempt for user {form_data.username} from IP {ip_address}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        if not admin.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin account is disabled",
            )

        access_token = create_admin_access_token(
            data={"sub": admin.username, "role": "super_admin"}
        )
        return {"access_token": access_token, "token_type": "bearer"}
