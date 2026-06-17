from pydantic import BaseModel


class LoginRequest(BaseModel):
    mobile: str
    hardware_id: str
    os_type: str = "unknown"
    device_name: str = "unknown"


class VerifyRequest(BaseModel):
    mobile: str
    code: str
    hardware_id: str
