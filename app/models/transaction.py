from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Float, DateTime, ForeignKey, JSON
from datetime import datetime, timezone
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    transaction_type: Mapped[str] = mapped_column(String(50), default="course_purchase")
    
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=True)
    license_id: Mapped[int] = mapped_column(ForeignKey("licenses.id"), nullable=True)
    
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    reference_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=True)
    gateway: Mapped[str] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    
    meta_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    course = relationship("Course")
    license = relationship("License")