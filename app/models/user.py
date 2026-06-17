from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    mobile = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    violation_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    otp_code = Column(String, nullable=True)
    otp_expire = Column(DateTime(timezone=True), nullable=True)

    devices = relationship(
        "Device", back_populates="user", cascade="all, delete-orphan"
    )
    licenses = relationship(
        "License", back_populates="user", cascade="all, delete-orphan"
    )
    hardware_resets = relationship(
        "HardwareReset", back_populates="user", cascade="all, delete-orphan"
    )

