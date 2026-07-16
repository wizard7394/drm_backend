from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class DeviceInfo(BaseModel):
    id: int
    hardware_id: str = Field(..., min_length=10, max_length=255)
    system_specs: Optional[str] = Field(default=None, max_length=1000)
    is_blocked: bool
    last_login: Optional[datetime] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class UserMonitoringResponse(BaseModel):
    id: int
    identifier: str = Field(..., min_length=5, max_length=255)
    email: Optional[str] = Field(default=None, max_length=255)
    first_name: Optional[str] = Field(default=None, max_length=50)
    last_name: Optional[str] = Field(default=None, max_length=50)
    is_active: bool
    devices: List[DeviceInfo] = Field(default_factory=list)


class BlockDeviceRequest(BaseModel):
    hardware_id: str = Field(..., min_length=10, max_length=255)
    reason: str = Field(..., min_length=1, max_length=500)


class ResetHardwareRequest(BaseModel):
    identifier: str = Field(..., min_length=5, max_length=255)
    reason: str = Field(..., min_length=1, max_length=500)
