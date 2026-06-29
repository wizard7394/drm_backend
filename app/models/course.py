from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import VaultBase


class Course(VaultBase):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    watermark_text = Column(String, nullable=True)
    watermark_color = Column(String, default="rgba(255,255,255,0.3)")
    is_active = Column(Boolean, default=True)
    base_stream_url = Column(String(500), nullable=True)

    nodes = relationship(
        "CourseNode", back_populates="course", cascade="all, delete-orphan"
    )


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
    attachment_url = Column(String, nullable=True)

    vault_id = Column(Integer, ForeignKey("vault_items.id"), nullable=True)

    course = relationship("Course", back_populates="nodes")
    parent = relationship("CourseNode", remote_side=[id])
    vault_item = relationship("VaultItem")
