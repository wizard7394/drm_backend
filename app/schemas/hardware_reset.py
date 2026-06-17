from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HardwareResetBase(BaseModel):
    license_id: int
    old_hardware_id: str
    new_hardware_id: str
    transaction_id: Optional[str] = None


class HardwareResetCreate(HardwareResetBase):
    user_id: int


class HardwareResetResponse(HardwareResetBase):
    id: int
    user_id: int
    reset_date: datetime

    class Config:
        from_attributes = True
