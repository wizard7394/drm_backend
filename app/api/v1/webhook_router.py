from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db
from app.services.webhook_service import WebhookService

router = APIRouter()


@router.post("/woocommerce")
async def woocommerce_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    event = request.headers.get("x-wc-webhook-event", "")
    if event == "ping":
        return {"status": "success", "message": "webhook_ping_successful"}

    payload = await request.body()
    signature = request.headers.get("x-wc-webhook-signature")

    return await WebhookService.process_woocommerce_webhook(payload, signature, db)
