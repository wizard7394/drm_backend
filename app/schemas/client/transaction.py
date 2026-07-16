from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TransactionCreate(BaseModel):
    amount: int
    transaction_type: str = Field(..., min_length=1, max_length=50)
    status: str = Field(..., min_length=1, max_length=50)
    reference_id: Optional[str] = Field(default=None, max_length=255)


class TransactionResponse(BaseModel):
    id: int
    amount: int
    transaction_type: str = Field(..., min_length=1, max_length=50)
    status: str = Field(..., min_length=1, max_length=50)
    reference_id: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
