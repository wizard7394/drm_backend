from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DeviceInfo(BaseModel):
    id: int
    hardware_id: str
    system_specs: Optional[str] = None
    is_blocked: bool
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserMonitoringResponse(BaseModel):
    id: int
    identifier: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    devices: List[DeviceInfo]


class BlockDeviceRequest(BaseModel):
    hardware_id: str
    reason: str


class ResetHardwareRequest(BaseModel):
    identifier: str
    reason: str
