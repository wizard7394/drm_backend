import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.license import License

async def seed_test_user():
    async with AsyncSessionLocal() as session:
        test_phone = "09367013231"
        
        user_query = await session.execute(select(User).where(User.phone_number == test_phone))
        user = user_query.scalars().first()
        
        if not user:
            user = User(phone_number=test_phone)
            session.add(user)
            await session.flush()
            print("Test user created successfully.")

        license_query = await session.execute(
            select(License).where(License.user_id == user.id, License.course_id == 13030)
        )
        lic = license_query.scalars().first()
        
        if not lic:
            lic = License(
                user_id=user.id,
                course_id=13030,
                license_key="PREMIUM-LIC-13030",
                is_revoked=False
            )
            session.add(lic)
            print("Premium license assigned to test user.")
            
        await session.commit()
        print("Database sync complete.")

if __name__ == "__main__":
    asyncio.run(seed_test_user())