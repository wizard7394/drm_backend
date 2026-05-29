from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class CourseVideoSchema(BaseModel):
    id: int
    title: str
    duration: int
    video_url: str
    sort_order: int
    
    model_config = ConfigDict(from_attributes=True)

class CourseSectionSchema(BaseModel):
    id: int
    title: str
    sort_order: int
    videos: List[CourseVideoSchema] = []
    
    model_config = ConfigDict(from_attributes=True)

class CourseSchema(BaseModel):
    id: int
    title: str
    watermark_text: Optional[str] = None
    watermark_color: str
    sections: List[CourseSectionSchema] = []
    
    model_config = ConfigDict(from_attributes=True)