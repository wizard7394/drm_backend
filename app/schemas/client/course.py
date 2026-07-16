from typing import List, Optional
from pydantic import BaseModel, Field


class ClientCourseItem(BaseModel):
    id: int
    title: str = Field(..., min_length=1, max_length=255)
    is_active: bool


class ClientCourseListResponse(BaseModel):
    status: str = Field(default="success", max_length=20)
    courses: List[ClientCourseItem] = Field(default_factory=list)


class VaultInfo(BaseModel):
    uuid: str = Field(..., min_length=36, max_length=36)
    file_hash: str = Field(..., min_length=32, max_length=128)
    download_url: Optional[str] = Field(default=None, max_length=1024)


class CourseNodeItem(BaseModel):
    id: int
    parent_id: Optional[int] = Field(default=None)
    item_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    sort_order: int
    duration: Optional[int] = Field(default=None)
    attachments: Optional[str] = Field(default=None, max_length=2048)
    vault: Optional[VaultInfo] = Field(default=None)
    children: List["CourseNodeItem"] = Field(default_factory=list)


class ClientCourseDetailsResponse(BaseModel):
    id: int
    title: str = Field(..., min_length=1, max_length=255)
    watermark_text: Optional[str] = Field(default=None, max_length=100)
    watermark_color: Optional[str] = Field(default=None, max_length=50)
    sections: List[CourseNodeItem] = Field(default_factory=list)


class WatchedVideoResponse(BaseModel):
    status: str = Field(default="success", max_length=20)


class WatchedVideosListResponse(BaseModel):
    status: str = Field(default="success", max_length=20)
    watched_uuids: List[str] = Field(default_factory=list)
