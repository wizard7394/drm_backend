from pydantic import BaseModel
from typing import Optional


class VideoManifestResponse(BaseModel):
    status: str = "success"
    video_id: int
    uuid: str
    file_hash: str
    aes_key: Optional[str] = None
    aes_iv: Optional[str] = None
