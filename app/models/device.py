from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    hardware_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    system_specs: Mapped[Optional[str]] = mapped_column(String(1000))
    os_type: Mapped[Optional[str]] = mapped_column(String(100))
    device_name: Mapped[Optional[str]] = mapped_column(String(100))
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    user: Mapped[Any] = relationship("User", back_populates="devices")
