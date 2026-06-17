from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    mobile: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    violation_count: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
