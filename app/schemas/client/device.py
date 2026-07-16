from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DeviceCreate(BaseModel):
    hardware_id: str = Field(..., min_length=10, max_length=255)
    os_type: Optional[str] = Field(default=None, max_length=50)
    device_name: Optional[str] = Field(default=None, max_length=255)


class DeviceResponse(BaseModel):
    id: int
    hardware_id: str = Field(..., min_length=10, max_length=255)
    os_type: Optional[str] = Field(default=None, max_length=50)
    device_name: Optional[str] = Field(default=None, max_length=255)
    is_blocked: bool
    created_at: datetime
    last_login: Optional[datetime] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)
