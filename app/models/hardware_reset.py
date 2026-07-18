from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class HardwareReset(Base):
    __tablename__ = "hardware_resets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    previous_hardware_id = Column(String(255), nullable=True)
    reason = Column(String(1000), nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    approved_by_admin_id = Column(
        Integer, ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="hardware_resets")
    admin = relationship("Admin", backref="approved_resets")
