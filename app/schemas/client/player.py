from typing import Optional
from pydantic import BaseModel, Field


class VideoManifestResponse(BaseModel):
    status: str = Field(default="success", max_length=20)
    video_id: int
    uuid: str = Field(..., min_length=36, max_length=36)
    file_hash: str = Field(..., min_length=32, max_length=128)
    aes_key: Optional[str] = Field(default=None, max_length=255)
    aes_iv: Optional[str] = Field(default=None, max_length=32)
