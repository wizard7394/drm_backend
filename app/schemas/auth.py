from pydantic import BaseModel
from pydantic import Field
from typing import Optional


class LoginRequest(BaseModel):
    mobile: str
    hardware_id: str
    os_type: str = "unknown"
    device_name: str = "unknown"


class VerifyRequest(BaseModel):
    mobile: str
    code: str
    hardware_id: str
    system_specs: Optional[str] = "Unknown"


class RequestOtpSchema(BaseModel):
    mobile: str = Field(..., description="User mobile number")
    hardware_id: str = Field(..., description="Unique hardware identifier")
    system_specs: Optional[str] = "Unknown"
