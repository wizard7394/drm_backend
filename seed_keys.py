import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.course import Course, CourseSection, CourseVideo
from app.models.user import User
from app.models.license import License
from app.models.device import HardwareDevice

async def seed_video_keys():
    print("Checking and creating missing tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        course_query = await session.execute(select(Course).where(Course.id == 13030))
        course = course_query.scalars().first()
        
        if not course:
            course = Course(id=13030, title="Premium Course 13030")
            session.add(course)
            await session.flush()

        section_query = await session.execute(select(CourseSection).where(CourseSection.course_id == 13030))
        section = section_query.scalars().first()

        if not section:
            section = CourseSection(id=1, course_id=13030, title="Main Section")
            session.add(section)
            await session.flush()

        video_query = await session.execute(select(CourseVideo).where(CourseVideo.id == 1))
        video = video_query.scalars().first()
        
        aes_key = "iWHLiAQTRnKzj7DvTwB3Jly8RtHpZ0fBm9Ja8Jvl4ms="
        aes_iv = "wWFENQMtnBUbvaMl"

        if video:
            video.section_id = section.id
            video.aes_key = aes_key
            video.aes_iv = aes_iv
            video.video_url = "http://localhost/dummy.mp6"
        else:
            video = CourseVideo(
                id=1,
                section_id=section.id,
                title="01.Start",
                video_url="http://localhost/dummy.mp6",
                aes_key=aes_key,
                aes_iv=aes_iv
            )
            session.add(video)
        
        await session.commit()
        print("Database updated successfully. Hierarchy and keys injected.")

if __name__ == "__main__":
    asyncio.run(seed_video_keys())