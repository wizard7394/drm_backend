from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.dependencies import get_db, get_current_user_token
from app.models.license import License

router = APIRouter()


@router.get("/my-courses")
async def fetch_user_courses(
    payload: dict = Depends(get_current_user_token), db: AsyncSession = Depends(get_db)
):
    user_id = int(payload.get("sub"))

    query = await db.execute(select(License).where(License.user_id == user_id))
    licenses = query.scalars().all()

    courses_data = []
    for lic in licenses:
        courses_data.append(
            {
                "id": str(lic.course_id),
                "title": f"Premium Course {lic.course_id}",
                "progress": 0.0,
                "image": "THUMBNAIL_PLACEHOLDER",
                "license_key": lic.license_key,
            }
        )

    return {"status": "success", "courses": courses_data}
