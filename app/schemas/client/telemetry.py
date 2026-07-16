from typing import List
from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    type: str = Field(..., max_length=50)
    video: str = Field(..., max_length=255)
    time: int = Field(..., ge=0)
    data: str = Field(..., max_length=500)


class TelemetryBatch(BaseModel):
    events: List[TelemetryEvent] = Field(..., max_length=50)
