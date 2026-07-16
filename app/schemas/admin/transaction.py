from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TransactionBase(BaseModel):
    amount: int
    transaction_type: str = Field(..., min_length=1, max_length=50)
    status: str = Field(..., min_length=1, max_length=50)
    reference_id: Optional[str] = Field(default=None, max_length=255)


class TransactionCreate(TransactionBase):
    user_id: int


class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
