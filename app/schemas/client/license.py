from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class LicenseCreate(BaseModel):
    course_id: int
    license_key: str = Field(..., min_length=10, max_length=255)


class LicenseResponse(BaseModel):
    id: int
    course_id: int
    license_key: str = Field(..., min_length=10, max_length=255)
    reset_count: int
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)
