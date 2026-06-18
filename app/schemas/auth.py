from pydantic import BaseModel
from pydantic import Field


class LoginRequest(BaseModel):
    mobile: str
    hardware_id: str
    os_type: str = "unknown"
    device_name: str = "unknown"


class VerifyRequest(BaseModel):
    mobile: str
    code: str
    hardware_id: str


class RequestOtpSchema(BaseModel):
    mobile: str = Field(..., description="User mobile number")
    hardware_id: str = Field(..., description="Unique hardware identifier")
