from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class LicenseBase(BaseModel):
    course_id: int
    license_key: str = Field(..., min_length=10, max_length=255)


class LicenseCreate(LicenseBase):
    user_id: int
    expires_at: Optional[datetime] = Field(default=None)


class LicenseResponse(LicenseBase):
    id: int
    user_id: int
    reset_count: int
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)
