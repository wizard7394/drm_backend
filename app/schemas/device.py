from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DeviceBase(BaseModel):
    hardware_id: str
    os_type: Optional[str] = None
    device_name: Optional[str] = None


class DeviceCreate(DeviceBase):
    user_id: int


class DeviceResponse(DeviceBase):
    id: int
    user_id: int
    is_blocked: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True
