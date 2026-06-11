import os
import hmac
import hashlib
import base64
import json
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import get_db
from app.schemas.webhook import WooCommerceOrder
from app.models.user import User
from app.models.license import License
from app.models.transaction import Transaction
from app.services.license_service import generate_license_key

router = APIRouter()
WOOCOMMERCE_SECRET = os.getenv("WOOCOMMERCE_SECRET")

@router.post("/woocommerce")
async def woocommerce_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    event = request.headers.get("x-wc-webhook-event", "")
    if event == "ping":
        return {"status": "success", "message": "Webhook ping successful."}

    payload = await request.body()
    signature = request.headers.get("x-wc-webhook-signature")
    
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature header")
        
    if not WOOCOMMERCE_SECRET:
        raise HTTPException(status_code=500, detail="Server configuration error: Missing Webhook Secret")

    expected_sig = hmac.new(
        WOOCOMMERCE_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256
    ).digest()
    
    expected_sig_b64 = base64.b64encode(expected_sig).decode("utf-8")
    
    if not hmac.compare_digest(signature, expected_sig_b64):
        raise HTTPException(status_code=403, detail="Invalid digital signature")
        
    order_data = json.loads(payload)
    
    if order_data.get("status") != "completed":
        print(f"Warning: Order {order_data.get('id')} ignored. Status: {order_data.get('status')}")
        return {"status": "ignored", "message": "Order is not completed yet."}
        
    order = WooCommerceOrder(**order_data)
    phone = order.billing.phone
    
    user_query = await db.execute(select(User).where(User.phone_number == phone))
    user = user_query.scalars().first()

    if not user:
        user = User(phone_number=phone)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    generated_licenses = []
    for item in order.line_items:
        new_license = License(
            user_id=user.id,
            license_key=generate_license_key(),
            course_id=item.product_id,
            max_devices=1
        )
        db.add(new_license)
        await db.flush()
        generated_licenses.append(new_license)
        
        new_transaction = Transaction(
            user_id=user.id,
            transaction_type="course_purchase",
            course_id=item.product_id,
            license_id=new_license.id,
            amount=float(order.total),
            reference_id=str(order.id),
            gateway="woocommerce",
            status="success",
            meta_data={"product_name": item.name, "wc_order_id": order.id}
        )
        db.add(new_transaction)

    await db.commit()
    print(f"Success! {len(generated_licenses)} licenses and transactions created for phone: {phone}")
    return {"status": "success", "message": f"Created {len(generated_licenses)} licenses."}