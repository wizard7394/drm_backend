import json
from typing import List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator


class CourseCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    watermark_text: Optional[str] = Field(default=None, max_length=100)
    watermark_color: Optional[str] = Field(default=None, max_length=50)
    is_active: bool = Field(default=True)


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=255)
    watermark_text: Optional[str] = Field(default=None, max_length=100)
    watermark_color: Optional[str] = Field(default=None, max_length=50)
    is_active: Optional[bool] = Field(default=None)


class NodeCreate(BaseModel):
    course_id: int
    parent_id: Optional[int] = Field(default=None)
    item_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    sort_order: int = Field(default=0)
    video_url: Optional[str] = Field(default=None, max_length=1024)
    duration: Optional[int] = Field(default=None)
    attachments: Optional[Union[List[Any], str]] = Field(default=None)
    vault_id: Optional[int] = Field(default=None)

    @field_validator("attachments", mode="before")
    @classmethod
    def parse_attachments(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValueError("invalid_json_format")
        return value


class NodeUpdate(BaseModel):
    parent_id: Optional[int] = Field(default=None)
    item_type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    sort_order: Optional[int] = Field(default=None)
    video_url: Optional[str] = Field(default=None, max_length=1024)
    duration: Optional[int] = Field(default=None)
    attachments: Optional[Union[List[Any], str]] = Field(default=None)
    vault_id: Optional[int] = Field(default=None)

    @field_validator("attachments", mode="before")
    @classmethod
    def parse_attachments(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValueError("invalid_json_format")
        return value


class VaultInjectItem(BaseModel):
    uuid: str = Field(..., min_length=36, max_length=36)
    original_filename: str = Field(..., min_length=1, max_length=255)
    file_hash: str = Field(..., min_length=32, max_length=128)
    encryption_key: Optional[str] = Field(default=None, max_length=255)
    decryption_key: Optional[str] = Field(default=None, max_length=255)
    aes_key: Optional[str] = Field(default=None, max_length=255)
    aes_iv: Optional[str] = Field(default=None, max_length=32)
    iv: Optional[str] = Field(default=None, max_length=32)
    duration: Optional[int] = Field(default=None)
    download_url: Optional[str] = Field(default=None, max_length=1024)


class VaultBulkInjectRequest(BaseModel):
    batch_name: str = Field(..., min_length=1, max_length=100)
    items: List[VaultInjectItem]


class TriggerAutobuildRequest(BaseModel):
    batch_name: str = Field(..., min_length=1, max_length=100)
