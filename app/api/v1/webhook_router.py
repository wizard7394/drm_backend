from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hmac
import hashlib
import base64
import json

from app.api.dependencies import get_db
from app.schemas.webhook import WooCommerceOrder
from app.models.user import User
from app.models.license import License
from app.services.license_service import generate_license_key

router = APIRouter()
WOOCOMMERCE_SECRET = "J7^jhdf912-_j2bch23Nh2mn@#$bhd53ksssHy3^51JK785v"

@router.post("/woocommerce")
async def woocommerce_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("x-wc-webhook-signature")
    
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
        
    expected_sig = hmac.new(
        WOOCOMMERCE_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256
    ).digest()
    
    expected_sig_b64 = base64.b64encode(expected_sig).decode("utf-8")
    
    if not hmac.compare_digest(signature, expected_sig_b64):
        raise HTTPException(status_code=403, detail="Invalid signature")
        
    order_data = json.loads(payload)
    order = WooCommerceOrder(**order_data)

    if order.status != "completed":
        return {"status": "ignored", "message": "Order is not completed yet."}

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
        generated_licenses.append(new_license)

    await db.commit()
    return {"status": "success", "message": f"Created {len(generated_licenses)} licenses for user."}