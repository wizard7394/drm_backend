from typing import List
from pydantic import BaseModel, Field


class WooCommerceBilling(BaseModel):
    phone: str = Field(..., min_length=5, max_length=20)


class WooCommerceLineItem(BaseModel):
    product_id: int
    name: str = Field(..., min_length=1, max_length=255)


class WooCommerceOrder(BaseModel):
    id: int
    status: str = Field(..., min_length=1, max_length=50)
    total: str = Field(..., min_length=1, max_length=50)
    billing: WooCommerceBilling
    line_items: List[WooCommerceLineItem] = Field(..., max_length=100)


class WebhookResponse(BaseModel):
    status: str = Field(default="success", max_length=50)
    message: str = Field(..., max_length=255)
