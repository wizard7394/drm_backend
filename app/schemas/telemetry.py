from pydantic import BaseModel
from typing import List

class HeatmapPayload(BaseModel):
    license_key: str
    video_id: int
    watched_seconds: List[int]