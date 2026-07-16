from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.license import License
    from app.models.hardware_reset import HardwareReset


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    mobile: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(50))
    last_name: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    violation_count: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    otp_code: Mapped[Optional[str]] = mapped_column(String(10))
    otp_expire: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    devices: Mapped[List["Device"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    licenses: Mapped[List["License"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    hardware_resets: Mapped[List["HardwareReset"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
