from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import VaultBase


class WatchedVideo(VaultBase):
    __tablename__ = "watched_videos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(index=True)
    vault_uuid: Mapped[str] = mapped_column(String(50), index=True)
    watched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Course(VaultBase):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(250), index=True)
    watermark_text: Mapped[Optional[str]] = mapped_column(String(250))
    watermark_color: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    base_stream_url: Mapped[Optional[str]] = mapped_column(String(500))

    nodes: Mapped[List["CourseNode"]] = relationship(
        "CourseNode", back_populates="course", cascade="all, delete"
    )


class CourseNode(VaultBase):
    __tablename__ = "course_nodes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("course_nodes.id"))
    item_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(250))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    video_url: Mapped[Optional[str]] = mapped_column(String(1000))
    duration: Mapped[Optional[int]] = mapped_column(Integer)
    attachments: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    vault_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vault_items.id"))

    course: Mapped["Course"] = relationship("Course", back_populates="nodes")
    parent: Mapped[Optional["CourseNode"]] = relationship(
        "CourseNode", remote_side=[id], cascade="all, delete"
    )
    vault_item: Mapped[Optional[Any]] = relationship("VaultItem")
