from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any


class CourseNodeSchema(BaseModel):
    id: int
    parent_id: Optional[int] = None
    vault_id: Optional[int] = None
    item_type: str
    title: str
    sort_order: int
    video_url: Optional[str] = None
    duration: Optional[int] = None
    attachments: Optional[List[Any]] = None
    children: List["CourseNodeSchema"] = []
    model_config = ConfigDict(from_attributes=True)


class CourseSchema(BaseModel):
    id: int
    title: str
    watermark_text: Optional[str] = None
    watermark_color: Optional[str] = None
    is_active: bool
    base_stream_url: Optional[str] = None
    nodes: List[CourseNodeSchema] = []
    model_config = ConfigDict(from_attributes=True)


class CourseCreate(BaseModel):
    title: str
    watermark_text: Optional[str] = None
    watermark_color: Optional[str] = None
    is_active: bool = True
    base_stream_url: Optional[str] = None


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    watermark_text: Optional[str] = None
    watermark_color: Optional[str] = None
    is_active: Optional[bool] = None
    base_stream_url: Optional[str] = None


class NodeCreate(BaseModel):
    course_id: int
    parent_id: Optional[int] = None
    item_type: str
    title: str
    sort_order: int
    video_url: Optional[str] = None
    duration: Optional[int] = None
    attachments: Optional[List[Any]] = None
    vault_id: Optional[int] = None


class NodeUpdate(BaseModel):
    title: Optional[str] = None
    sort_order: Optional[int] = None
    video_url: Optional[str] = None
    duration: Optional[int] = None
    attachments: Optional[List[Any]] = None
    vault_id: Optional[int] = None


class AutoBuildRequest(BaseModel):
    course_id: int
    batch_name: str
