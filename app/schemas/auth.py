from pydantic import BaseModel

class HardwareAuthRequest(BaseModel):
    license_key: str
    hardware_hash: str
    platform: str

class AuthResponse(BaseModel):
    status: str
    access_token: str
    message: str
    
class SignedAuthResponse(BaseModel):
    payload: AuthResponse
    signature: str    