from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UnauthorizedAttempt(Base):
    __tablename__ = "unauthorized_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    identifier: Mapped[str] = mapped_column(String(255), index=True)
    hardware_id: Mapped[str] = mapped_column(String(255), index=True)
    ip_address: Mapped[str] = mapped_column(String(50))
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class BlacklistedHardware(Base):
    __tablename__ = "blacklisted_hardware"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hardware_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    reason: Mapped[str] = mapped_column(String(500))
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DeviceAuditLog(Base):
    __tablename__ = "device_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    identifier: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    hardware_id: Mapped[str] = mapped_column(String(255), index=True)
    action: Mapped[str] = mapped_column(String(500))
    reason: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
