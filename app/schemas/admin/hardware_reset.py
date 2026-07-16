from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class HardwareResetBase(BaseModel):
    license_id: int
    old_hardware_id: str = Field(..., min_length=10, max_length=255)
    new_hardware_id: str = Field(..., min_length=10, max_length=255)
    transaction_id: Optional[str] = Field(default=None, max_length=100)


class HardwareResetCreate(HardwareResetBase):
    user_id: int


class HardwareResetResponse(HardwareResetBase):
    id: int
    user_id: int
    reset_date: datetime

    model_config = ConfigDict(from_attributes=True)
