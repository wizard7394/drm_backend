from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class HardwareReset(Base):
    __tablename__ = "hardware_resets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False)
    old_hardware_id = Column(String, nullable=False)
    new_hardware_id = Column(String, nullable=False)
    transaction_id = Column(String, nullable=True)
    reset_date = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="hardware_resets")
    license = relationship("License", back_populates="hardware_resets")
