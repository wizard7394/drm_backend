from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserCreateAdmin(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=15)
    is_active: bool = Field(default=True)


class UserUpdateAdmin(BaseModel):
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[EmailStr] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class UserListItem(BaseModel):
    id: int
    mobile: str = Field(..., min_length=10, max_length=15)
    name: str = Field(..., max_length=200)
    email: Optional[str] = Field(default=None, max_length=255)
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    users: List[UserListItem] = Field(default_factory=list)


class AdminUserProfileResponse(BaseModel):
    id: int
    mobile: str = Field(..., min_length=10, max_length=15)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    violation_count: int = Field(default=0, ge=0)
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class HeatmapItem(BaseModel):
    vault_uuid: str = Field(..., min_length=36, max_length=36)
    watched_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserHeatmapResponse(BaseModel):
    heatmap: List[HeatmapItem] = Field(default_factory=list)


class AdminTransactionItem(BaseModel):
    id: int
    amount: int = Field(..., ge=0)
    status: str = Field(..., max_length=50)

    model_config = ConfigDict(from_attributes=True)


class UserTransactionsResponse(BaseModel):
    transactions: List[AdminTransactionItem] = Field(default_factory=list)


class AdminCourseItem(BaseModel):
    id: int
    title: str = Field(..., max_length=255)

    model_config = ConfigDict(from_attributes=True)


class UserCoursesResponse(BaseModel):
    courses: List[AdminCourseItem] = Field(default_factory=list)


class AdminDeviceItem(BaseModel):
    id: int
    hardware_id: str
    system_specs: Optional[str] = None
    os_type: Optional[str] = None
    device_name: Optional[str] = None
    is_blocked: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserDevicesResponse(BaseModel):
    devices: List[AdminDeviceItem] = Field(default_factory=list)


class AdminUserLogItem(BaseModel):
    id: int
    hardware_id: str
    action: str
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogsResponse(BaseModel):
    logs: List[AdminUserLogItem] = Field(default_factory=list)
