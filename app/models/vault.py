from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class VideoVault(Base):
    __tablename__ = "video_vault"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    batch_name = Column(String, index=True, nullable=False)
    uuid = Column(String, unique=True, index=True, nullable=False)
    original_filename = Column(String, nullable=True)
    file_hash = Column(String, nullable=False)
    aes_key = Column(String, nullable=False)
    aes_iv = Column(String, nullable=False)
    download_url = Column(String, nullable=True)
    status = Column(String, default="unused")
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="vault_items")
