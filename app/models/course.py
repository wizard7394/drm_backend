from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref
from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    watermark_text = Column(String, nullable=True)
    watermark_color = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    nodes = relationship(
        "CourseNode", back_populates="course", cascade="all, delete-orphan"
    )


class CourseNode(Base):
    __tablename__ = "course_nodes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    parent_id = Column(
        Integer, ForeignKey("course_nodes.id", ondelete="CASCADE"), nullable=True
    )

    item_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    sort_order = Column(Integer, default=1)

    video_url = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)
    aes_key = Column(String, nullable=True)
    aes_iv = Column(String, nullable=True)

    course = relationship("Course", back_populates="nodes")
    children = relationship(
        "CourseNode",
        backref=backref("parent", remote_side=[id]),
        cascade="all, delete-orphan",
    )
