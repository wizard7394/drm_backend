from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    mobile: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserCreateAdmin(BaseModel):
    mobile: str
    is_active: bool = True


class UserUpdateAdmin(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserListItem(BaseModel):
    id: int
    mobile: str
    name: str
    email: str
    is_active: bool


class UserListResponse(BaseModel):
    users: List[UserListItem]


class UserProfileResponse(BaseModel):
    id: int
    mobile: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    violation_count: int
    is_active: bool


class HeatmapItem(BaseModel):
    vault_uuid: str
    watched_at: datetime


class UserHeatmapResponse(BaseModel):
    heatmap: List[HeatmapItem]


class TransactionItem(BaseModel):
    id: int
    amount: float
    status: str


class UserTransactionsResponse(BaseModel):
    transactions: List[TransactionItem]


class CourseItem(BaseModel):
    id: int
    title: str


class UserCoursesResponse(BaseModel):
    courses: List[CourseItem]
