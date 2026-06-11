from pydantic import BaseModel

class WooCommerceBilling(BaseModel):
    phone: str

class WooCommerceLineItem(BaseModel):
    product_id: int
    name: str

class WooCommerceOrder(BaseModel):
    id: int
    status: str
    total: str
    billing: WooCommerceBilling
    line_items: list[WooCommerceLineItem]

class WebhookResponse(BaseModel):
    status: str
    message: str