from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LicenseBase(BaseModel):
    course_id: int
    license_key: str


class LicenseCreate(LicenseBase):
    user_id: int
    expires_at: Optional[datetime] = None


class LicenseResponse(LicenseBase):
    id: int
    user_id: int
    reset_count: int
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True
