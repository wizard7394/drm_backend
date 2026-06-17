from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AdminBase(BaseModel):
    username: str
    role: Optional[str] = "super_admin"


class AdminCreate(AdminBase):
    password: str


class AdminResponse(AdminBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
