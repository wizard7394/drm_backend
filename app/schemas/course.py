from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class CourseNodeSchema(BaseModel):
    id: int
    parent_id: Optional[int] = None
    vault_id: Optional[int] = None
    item_type: str
    title: str
    sort_order: int
    video_url: Optional[str] = None
    duration: Optional[int] = None
    attachment_url: Optional[str] = None

    children: List["CourseNodeSchema"] = []

    model_config = ConfigDict(from_attributes=True)


class CourseSchema(BaseModel):
    id: int
    title: str
    watermark_text: Optional[str] = None
    watermark_color: Optional[str] = None
    is_active: bool

    nodes: List[CourseNodeSchema] = []

    model_config = ConfigDict(from_attributes=True)
