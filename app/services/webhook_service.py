import os
import hmac
import hashlib
import base64
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.license import License

logger = logging.getLogger(__name__)

PRODUCT_MAP = {
    "1174": 1,
}


class WebhookService:
    @staticmethod
    async def process_woocommerce_webhook(
        payload: bytes, signature: str, db: AsyncSession
    ):
        secret_key = os.getenv("WOOCOMMERCE_SECRET", "")
        if not secret_key:
            logger.error("WooCommerce webhook secret is not configured")
            raise Exception("Server configuration error")

        webhook_secret = secret_key.encode("utf-8")
        hmac_digest = hmac.new(webhook_secret, payload, hashlib.sha256).digest()
        expected_signature = base64.b64encode(hmac_digest).decode("utf-8")

        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("Invalid webhook signature detected")
            raise Exception("Invalid signature")

        data = json.loads(payload)
        status = data.get("status")

        if status not in ["processing", "completed"]:
            return {"status": "ignored", "message": f"Order status is {status}"}

        billing = data.get("billing", {})
        mobile = billing.get("phone")
        first_name = billing.get("first_name") or "Unknown"
        last_name = billing.get("last_name") or "Unknown"
        email = billing.get("email") or ""

        if not mobile:
            raise Exception("No phone number found in payload")

        user_stmt = select(User).where(User.mobile == mobile)
        user_res = await db.execute(user_stmt)
        user = user_res.scalars().first()

        if not user:
            user = User(
                mobile=mobile,
                first_name=first_name,
                last_name=last_name,
                email=email,
                is_active=True,
            )
            db.add(user)
            await db.flush()
        else:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            await db.flush()

        line_items = data.get("line_items", [])
        for item in line_items:
            wc_product_id = str(item.get("product_id"))
            course_id = PRODUCT_MAP.get(wc_product_id)

            if course_id:
                existing_license_stmt = select(License).where(
                    License.user_id == user.id, License.course_id == course_id
                )
                license_res = await db.execute(existing_license_stmt)

                if not license_res.scalars().first():
                    new_license = License(
                        user_id=user.id, course_id=course_id, is_active=True
                    )
                    db.add(new_license)

        await db.commit()
        return {"status": "success", "message": "Data processed"}
