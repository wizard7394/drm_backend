from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from app.core.database import Base


class UnauthorizedAttempt(Base):
    __tablename__ = "unauthorized_attempts"

    id = Column(Integer, primary_key=True, index=True)
    mobile = Column(String(20), index=True)
    hardware_id = Column(String(255), index=True)
    ip_address = Column(String(50), index=True)
    attempted_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class BlacklistedHardware(Base):
    __tablename__ = "blacklisted_hardware"

    id = Column(Integer, primary_key=True, index=True)
    hardware_id = Column(String(255), unique=True, index=True)
    reason = Column(String(255))
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
