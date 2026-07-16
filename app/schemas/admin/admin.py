from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class AdminBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    role: Optional[str] = Field(default="super_admin", max_length=20)


class AdminCreate(AdminBase):
    password: str = Field(..., min_length=8, max_length=128)


class AdminResponse(AdminBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
