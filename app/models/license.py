from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime
from datetime import datetime, timezone
from app.core.database import Base

class License(Base):
    __tablename__ = "licenses"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    license_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    course_id: Mapped[int] = mapped_column(Integer, index=True)
    transaction_id: Mapped[str] = mapped_column(String(100), nullable=True)
    max_devices: Mapped[int] = mapped_column(Integer, default=1)
    reset_count: Mapped[int] = mapped_column(Integer, default=0)
    purchase_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    user = relationship("User", back_populates="licenses")
    devices = relationship("HardwareDevice", back_populates="license", cascade="all, delete-orphan")
    reset_logs = relationship("HardwareResetLog", back_populates="license", cascade="all, delete-orphan")