from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.user import User
from app.models.transaction import Transaction
from app.models.course import Course, WatchedVideo
from app.models.license import License
from app.schemas.admin.user import UserCreateAdmin, UserUpdateAdmin


class AdminUserService:
    @staticmethod
    async def get_all_users(db: AsyncSession):
        result = await db.execute(select(User).order_by(desc(User.id)))
        users = result.scalars().all()
        return {
            "users": [
                {
                    "id": u.id,
                    "mobile": u.mobile,
                    "name": f"{u.first_name or ''} {u.last_name or ''}".strip()
                    or "UNKNOWN",
                    "email": u.email or "NO EMAIL",
                    "is_active": u.is_active,
                }
                for u in users
            ]
        }

    @staticmethod
    async def create_user(payload: UserCreateAdmin, db: AsyncSession):
        existing_query = await db.execute(
            select(User).where(User.mobile == payload.mobile)
        )
        if existing_query.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
            )

        new_user = User(mobile=payload.mobile, is_active=payload.is_active)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return {"status": "success", "user_id": new_user.id}

    @staticmethod
    async def update_user(user_id: int, payload: UserUpdateAdmin, db: AsyncSession):
        query = await db.execute(select(User).where(User.id == user_id))
        user = query.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        await db.commit()
        return {"status": "success"}

    @staticmethod
    async def get_user_profile(user_id: int, db: AsyncSession):
        query = await db.execute(select(User).where(User.id == user_id))
        user = query.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return {
            "id": user.id,
            "mobile": user.mobile,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "violation_count": user.violation_count,
            "is_active": user.is_active,
        }

    @staticmethod
    async def get_user_heatmap(user_id: int, vault_db: AsyncSession):
        query = await vault_db.execute(
            select(WatchedVideo).where(WatchedVideo.user_id == user_id)
        )
        watched_logs = query.scalars().all()
        return {
            "heatmap": [
                {"vault_uuid": w.vault_uuid, "watched_at": w.watched_at}
                for w in watched_logs
            ]
        }

    @staticmethod
    async def get_user_transactions(user_id: int, db: AsyncSession):
        query = await db.execute(
            select(Transaction).where(Transaction.user_id == user_id)
        )
        transactions = query.scalars().all()
        return {
            "transactions": [
                {
                    "id": t.id,
                    "amount": getattr(t, "amount", 0),
                    "status": getattr(t, "status", "unknown"),
                }
                for t in transactions
            ]
        }

    @staticmethod
    async def get_user_courses(user_id: int, db: AsyncSession, vault_db: AsyncSession):
        stmt = select(License.course_id).where(
            License.user_id == user_id, License.is_active
        )
        result = await db.execute(stmt)
        course_ids = result.scalars().all()

        if not course_ids:
            return {"courses": []}

        course_stmt = select(Course).where(Course.id.in_(course_ids))
        course_res = await vault_db.execute(course_stmt)
        courses = course_res.scalars().all()

        return {"courses": [{"id": c.id, "title": c.title} for c in courses]}
