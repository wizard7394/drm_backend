import hmac
import hashlib
import base64
import json
from fastapi import APIRouter, Header, Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import os
from app.core.database import get_db
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


async def verify_woocommerce_signature(
    request: Request, x_wc_webhook_signature: str = Header(None)
):
    secret = os.getenv("WOOCOMMERCE_SECRET")

    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security configuration missing",
        )

    if not x_wc_webhook_signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing webhook signature"
        )

    raw_body = await request.body()

    expected_mac = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()

    expected_signature = base64.b64encode(expected_mac).decode()

    if not hmac.compare_digest(expected_signature, x_wc_webhook_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature mismatch"
        )

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed JSON payload"
        )

    return payload


@router.post("/woocommerce")
async def woocommerce_handler(
    payload: dict = Depends(verify_woocommerce_signature),
    db: AsyncSession = Depends(get_db),
):
    order_id = payload.get("id")

    if not order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Payload missing order ID"
        )

    await WebhookService.process_order(db, payload, order_id)

    return {"status": "success"}
