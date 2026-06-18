import os
import hmac
import hashlib
import base64
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.webhook import WooCommerceOrder
from app.models.user import User
from app.models.license import License
from app.models.transaction import Transaction
from app.core.errors import AppErrors
from app.services.license_service import generate_license_key

WOOCOMMERCE_SECRET = os.getenv("WOOCOMMERCE_SECRET")


class WebhookService:
    @staticmethod
    async def process_woocommerce_webhook(
        payload: bytes, signature: str, db: AsyncSession
    ):
        if not signature:
            raise AppErrors.WEBHOOK_MISSING_SIGNATURE

        if not WOOCOMMERCE_SECRET:
            raise AppErrors.SERVER_CONFIG_ERROR

        expected_sig = hmac.new(
            WOOCOMMERCE_SECRET.encode("utf-8"), payload, hashlib.sha256
        ).digest()

        expected_sig_b64 = base64.b64encode(expected_sig).decode("utf-8")

        if not hmac.compare_digest(signature, expected_sig_b64):
            raise AppErrors.WEBHOOK_INVALID_SIGNATURE

        order_data = json.loads(payload)

        if order_data.get("status") != "completed":
            return {"status": "ignored", "message": "order_is_not_completed"}

        order = WooCommerceOrder(**order_data)
        phone = order.billing.phone
        first_name = order.billing.first_name
        last_name = order.billing.last_name
        email = order.billing.email

        user_query = await db.execute(select(User).where(User.mobile == phone))
        user = user_query.scalars().first()

        if not user:
            user = User(
                mobile=phone, first_name=first_name, last_name=last_name, email=email
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        generated_licenses = []
        for item in order.line_items:
            license_key = generate_license_key()

            new_license = License(
                user_id=user.id, course_id=item.product_id, license_key=license_key
            )
            db.add(new_license)
            await db.flush()
            generated_licenses.append(new_license)

            new_transaction = Transaction(
                user_id=user.id,
                transaction_type="course_purchase",
                amount=float(order.total),
                reference_id=str(order.id),
                status="success",
            )
            db.add(new_transaction)

        await db.commit()
        return {
            "status": "success",
            "message": f"generated_{len(generated_licenses)}_licenses",
        }
