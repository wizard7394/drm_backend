from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.dependencies import get_db
from app.schemas.webhook import WooCommerceOrder
from app.models.user import User
from app.models.license import License
from app.services.license_service import generate_license_key

router = APIRouter()

@router.post("/woocommerce")
async def woocommerce_webhook(order: WooCommerceOrder, db: AsyncSession = Depends(get_db)):
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