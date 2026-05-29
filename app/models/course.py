from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Boolean
from app.core.database import Base

class Course(Base):
    __tablename__ = "courses"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    watermark_text: Mapped[str] = mapped_column(String(255), nullable=True)
    watermark_color: Mapped[str] = mapped_column(String(50), default="rgba(255, 255, 255, 0.5)")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    sections = relationship("CourseSection", back_populates="course", cascade="all, delete-orphan", order_by="CourseSection.sort_order")

class CourseSection(Base):
    __tablename__ = "course_sections"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    title: Mapped[str] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    course = relationship("Course", back_populates="sections")
    videos = relationship("CourseVideo", back_populates="section", cascade="all, delete-orphan", order_by="CourseVideo.sort_order")

class CourseVideo(Base):
    __tablename__ = "course_videos"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("course_sections.id"))
    title: Mapped[str] = mapped_column(String(255))
    duration: Mapped[int] = mapped_column(Integer, default=0)
    video_url: Mapped[str] = mapped_column(String(1024))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    section = relationship("CourseSection", back_populates="videos")