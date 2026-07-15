from typing import List, Optional
from pydantic import BaseModel


class CourseCreate(BaseModel):
    title: str
    watermark_text: Optional[str] = None
    watermark_color: Optional[str] = None
    is_active: bool = True


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    watermark_text: Optional[str] = None
    watermark_color: Optional[str] = None
    is_active: Optional[bool] = None


class NodeCreate(BaseModel):
    course_id: int
    parent_id: Optional[int] = None
    item_type: str
    title: str
    sort_order: int = 0
    video_url: Optional[str] = None
    duration: Optional[int] = None
    attachments: Optional[str] = None
    vault_id: Optional[int] = None


class NodeUpdate(BaseModel):
    parent_id: Optional[int] = None
    item_type: Optional[str] = None
    title: Optional[str] = None
    sort_order: Optional[int] = None
    video_url: Optional[str] = None
    duration: Optional[int] = None
    attachments: Optional[str] = None
    vault_id: Optional[int] = None


class VaultInjectItem(BaseModel):
    uuid: str
    original_filename: str
    file_hash: str
    encryption_key: Optional[str] = None
    decryption_key: Optional[str] = None
    aes_key: Optional[str] = None
    aes_iv: Optional[str] = None
    iv: Optional[str] = None
    duration: Optional[int] = None
    download_url: Optional[str] = None


class VaultBulkInjectRequest(BaseModel):
    batch_name: str
    items: List[VaultInjectItem]


class TriggerAutobuildRequest(BaseModel):
    batch_name: str


class ClientCourseItem(BaseModel):
    id: int
    title: str
    is_active: bool


class ClientCourseListResponse(BaseModel):
    status: str = "success"
    courses: List[ClientCourseItem]


class VaultInfo(BaseModel):
    uuid: str
    file_hash: str
    download_url: Optional[str] = None


class CourseNodeItem(BaseModel):
    id: int
    parent_id: Optional[int] = None
    item_type: str
    title: str
    sort_order: int
    duration: Optional[int] = None
    attachments: Optional[str] = None
    vault: Optional[VaultInfo] = None
    children: List["CourseNodeItem"] = []


class ClientCourseDetailsResponse(BaseModel):
    id: int
    title: str
    watermark_text: Optional[str] = None
    watermark_color: Optional[str] = None
    sections: List[CourseNodeItem]


class WatchedVideoResponse(BaseModel):
    status: str = "success"


class WatchedVideosListResponse(BaseModel):
    status: str = "success"
    watched_uuids: List[str]
