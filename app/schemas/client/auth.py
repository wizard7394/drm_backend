from typing import Optional
from pydantic import BaseModel, Field


class RequestOtpSchema(BaseModel):
    identifier: str = Field(
        ..., min_length=5, max_length=255, description="User mobile number or email"
    )
    hardware_id: str = Field(
        ..., min_length=10, max_length=255, description="Unique hardware identifier"
    )
    system_specs: Optional[str] = Field(default="Unknown", max_length=1000)


class VerifyRequest(BaseModel):
    identifier: str = Field(..., min_length=5, max_length=255)
    code: Optional[str] = Field(default=None, max_length=6)
    password: Optional[str] = Field(default=None, max_length=128)
    hardware_id: str = Field(..., min_length=10, max_length=255)
    system_specs: Optional[str] = Field(default="Unknown", max_length=1000)
