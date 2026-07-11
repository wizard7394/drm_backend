from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import VaultBase


class WatchedVideo(VaultBase):
    __tablename__ = "watched_videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    vault_uuid = Column(String, index=True)
    watched_at = Column(DateTime(timezone=True), server_default=func.now())


class Course(VaultBase):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    watermark_text = Column(String, nullable=True)
    watermark_color = Column(String, nullable=True)
    is_active = Column(Integer, default=1)
    base_stream_url = Column(String(500), nullable=True)

    nodes = relationship("CourseNode", back_populates="course", cascade="all, delete")


class CourseNode(VaultBase):
    __tablename__ = "course_nodes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    parent_id = Column(Integer, ForeignKey("course_nodes.id"), nullable=True)
    item_type = Column(String)
    title = Column(String)
    sort_order = Column(Integer, default=0)

    video_url = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)
    attachments = Column(JSON, nullable=True)

    vault_id = Column(Integer, ForeignKey("vault_items.id"), nullable=True)

    course = relationship("Course", back_populates="nodes")
    parent = relationship("CourseNode", remote_side=[id], cascade="all, delete")
    vault_item = relationship("VaultItem")
