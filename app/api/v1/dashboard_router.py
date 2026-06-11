from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.dependencies import get_current_user_token, get_db
from app.models.course import Course, CourseSection, CourseVideo
from app.models.license import License
from app.models.user import User
from app.models.transaction import Transaction

router = APIRouter()

@router.get("/my-courses")
async def get_my_courses(
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    user_id = int(token_data.get("sub"))
    
    query = await db.execute(select(License).where(License.user_id == user_id))
    licenses = query.scalars().all()

    courses = []
    for lic in licenses:
        course_query = await db.execute(select(Course).where(Course.id == lic.course_id))
        course = course_query.scalars().first()
        if course:
            courses.append({
                "id": course.id,
                "title": course.title,
                "license_key": lic.license_key
            })

    return {"status": "success", "courses": courses}


@router.get("/course-content/{course_id}")
async def get_course_details(
    course_id: int,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    user_id = int(token_data.get("sub"))
    
    license_query = await db.execute(select(License).where(
        License.user_id == user_id, 
        License.course_id == course_id
    ))
    
    if not license_query.scalars().first():
        raise HTTPException(status_code=403, detail="Access denied for this course")

    sections_query = await db.execute(select(CourseSection).where(CourseSection.course_id == course_id))
    sections = sections_query.scalars().all()

    result = []
    for sec in sections:
        vids_query = await db.execute(select(CourseVideo).where(CourseVideo.section_id == sec.id))
        vids = vids_query.scalars().all()
        
        video_list = []
        for v in vids:
            video_list.append({
                "id": v.id,
                "title": v.title,
                "description": "Premium video content and technical explanations for this session.",
            })
            
        result.append({
            "id": sec.id,
            "title": sec.title,
            "videos": video_list
        })

    return {"status": "success", "sections": result}


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    users_query = await db.execute(select(func.count(User.id)))
    total_users = users_query.scalar() or 0

    licenses_query = await db.execute(select(func.count(License.id)))
    total_licenses = licenses_query.scalar() or 0

    courses_query = await db.execute(select(func.count(Course.id)))
    total_courses = courses_query.scalar() or 0

    recent_tx_query = await db.execute(
        select(Transaction, User, Course)
        .join(User, Transaction.user_id == User.id)
        .join(Course, Transaction.course_id == Course.id, isouter=True)
        .order_by(Transaction.created_at.desc())
        .limit(5)
    )
    
    recent_records = recent_tx_query.all()
    recent_transactions = []
    
    for tx, usr, crs in recent_records:
        recent_transactions.append({
            "status": tx.status,
            "user": usr.phone_number if usr.phone_number else "Unknown",
            "course": crs.title if crs else tx.transaction_type,
            "amount": str(tx.amount)
        })

    return {
        "status": "success",
        "total_users": total_users,
        "total_licenses": total_licenses,
        "total_courses": total_courses,
        "recent_transactions": recent_transactions
    }