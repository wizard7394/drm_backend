from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[EmailStr] = Field(default=None)


class ClientUserProfileResponse(BaseModel):
    id: int
    mobile: str = Field(..., min_length=10, max_length=15)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)

    model_config = ConfigDict(from_attributes=True)


class ClientTransactionItem(BaseModel):
    id: int
    amount: int = Field(..., ge=0)
    status: str = Field(..., max_length=50)

    model_config = ConfigDict(from_attributes=True)


class ClientTransactionsResponse(BaseModel):
    transactions: List[ClientTransactionItem] = Field(default_factory=list)


class ClientCourseItem(BaseModel):
    id: int
    title: str = Field(..., max_length=255)

    model_config = ConfigDict(from_attributes=True)


class ClientCoursesResponse(BaseModel):
    courses: List[ClientCourseItem] = Field(default_factory=list)
