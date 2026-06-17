from pydantic import BaseModel
from typing import List


class TelemetryEvent(BaseModel):
    type: str
    video: str
    time: int
    data: str


class TelemetryBatch(BaseModel):
    events: List[TelemetryEvent]
