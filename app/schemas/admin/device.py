from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DeviceBase(BaseModel):
    hardware_id: str = Field(..., min_length=10, max_length=255)
    os_type: Optional[str] = Field(default=None, max_length=50)
    device_name: Optional[str] = Field(default=None, max_length=255)


class DeviceCreate(DeviceBase):
    user_id: int


class DeviceResponse(DeviceBase):
    id: int
    user_id: int
    is_blocked: bool
    created_at: datetime
    last_login: Optional[datetime] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)
