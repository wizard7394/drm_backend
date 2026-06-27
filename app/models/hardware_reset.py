from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean  # noqa: F401
from sqlalchemy.orm import relationship
from app.core.database import Base


class HardwareReset(Base):
    __tablename__ = "hardware_resets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    license_id = Column(Integer, index=True)

    old_hardware_id = Column(String)
    new_hardware_id = Column(String)
    status = Column(String, default="pending")
    requested_at = Column(DateTime)
    approved_at = Column(DateTime, nullable=True)

    user = relationship("User")
