from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Boolean, DateTime
from datetime import datetime, timezone
from app.core.database import Base

class HardwareDevice(Base):
    __tablename__ = "hardware_devices"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    license_id: Mapped[int] = mapped_column(ForeignKey("licenses.id"))
    hardware_hash: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    platform: Mapped[str] = mapped_column(String(50))
    last_online: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    license = relationship("License", back_populates="devices")

class HardwareResetLog(Base):
    __tablename__ = "hardware_reset_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    license_id: Mapped[int] = mapped_column(ForeignKey("licenses.id"))
    old_hardware_hash: Mapped[str] = mapped_column(String(256), nullable=True)
    reset_reason: Mapped[str] = mapped_column(String(255), nullable=True)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    reset_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    license = relationship("License", back_populates="reset_logs")