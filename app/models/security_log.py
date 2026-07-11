from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from app.core.database import Base


def get_naive_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UnauthorizedAttempt(Base):
    __tablename__ = "unauthorized_attempts"
    id = Column(Integer, primary_key=True, index=True)
    mobile = Column(String, index=True)
    hardware_id = Column(String, index=True)
    ip_address = Column(String)
    attempted_at = Column(DateTime, default=get_naive_utc_now)


class BlacklistedHardware(Base):
    __tablename__ = "blacklisted_hardware"
    id = Column(Integer, primary_key=True, index=True)
    hardware_id = Column(String, unique=True, index=True)
    reason = Column(String)
    added_at = Column(DateTime, default=get_naive_utc_now)


class DeviceAuditLog(Base):
    __tablename__ = "device_audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    mobile = Column(String, index=True, nullable=True)
    hardware_id = Column(String, index=True)
    action = Column(String)
    reason = Column(String)
    created_at = Column(DateTime, default=get_naive_utc_now)
