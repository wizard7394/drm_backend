from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class SecurityLogItem(BaseModel):
    id: int
    mobile: Optional[str] = None
    ip_address: Optional[str] = None
    hardware_id: Optional[str] = None
    attempted_at: datetime

    class Config:
        from_attributes = True


class DashboardStatsResponse(BaseModel):
    total_users: int
    total_courses: int
    total_active_licenses: int
    total_revenue: float
    recent_logs: List[SecurityLogItem]
