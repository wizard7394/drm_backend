from pydantic import BaseModel
from typing import Optional

class CreateCourseRequest(BaseModel):
    title: str
    watermark_text: Optional[str] = None
    watermark_color: str = "rgba(255, 255, 255, 0.5)"

class CreateSectionRequest(BaseModel):
    course_id: int
    title: str
    sort_order: int = 0

class CreateVideoRequest(BaseModel):
    section_id: int
    title: str
    duration: int
    video_url: str
    sort_order: int = 0