from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class SecurityLogItem(BaseModel):
    id: int
    mobile: Optional[str] = Field(default=None, max_length=15)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    hardware_id: Optional[str] = Field(default=None, max_length=255)
    attempted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardStatsResponse(BaseModel):
    total_users: int
    total_courses: int
    total_active_licenses: int
    total_revenue: int
    recent_logs: List[SecurityLogItem] = Field(default_factory=list)
