from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, DateTime, String
from datetime import datetime, timezone
from app.core.database import Base

class WatchHistory(Base):
    __tablename__ = "watch_history"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    video_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    play_count: Mapped[int] = mapped_column(Integer, default=1)
    last_played: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="watch_logs")

class VideoHeatmap(Base):
    __tablename__ = "video_heatmaps"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("course_videos.id"), index=True)
    license_id: Mapped[int] = mapped_column(ForeignKey("licenses.id"), index=True)
    watched_second: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))