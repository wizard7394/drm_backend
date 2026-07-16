from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class HardwareResetCreate(BaseModel):
    license_id: int
    old_hardware_id: str = Field(..., min_length=10, max_length=255)
    new_hardware_id: str = Field(..., min_length=10, max_length=255)
    transaction_id: Optional[str] = Field(default=None, max_length=100)


class HardwareResetResponse(BaseModel):
    id: int
    license_id: int
    old_hardware_id: str = Field(..., min_length=10, max_length=255)
    new_hardware_id: str = Field(..., min_length=10, max_length=255)
    transaction_id: Optional[str] = Field(default=None, max_length=100)
    reset_date: datetime

    model_config = ConfigDict(from_attributes=True)
