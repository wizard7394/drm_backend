from pydantic import BaseModel, Field
from typing import List


class TelemetryEvent(BaseModel):
    type: str = Field(..., max_length=50)
    video: str = Field(..., max_length=100)
    time: int
    data: str = Field(..., max_length=500)


class TelemetryBatch(BaseModel):
    events: List[TelemetryEvent] = Field(..., max_items=50)
