from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.api.dependencies import get_db
from app.models.course import Course, CourseNode
from app.models.user import User
from app.models.license import License

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    courses_count = await db.scalar(select(func.count(Course.id)))
    folders_count = await db.scalar(
        select(func.count(CourseNode.id)).where(CourseNode.item_type == "folder")
    )
    videos_count = await db.scalar(
        select(func.count(CourseNode.id)).where(CourseNode.item_type == "video")
    )
    users_count = await db.scalar(select(func.count(User.id)))
    licenses_count = await db.scalar(select(func.count(License.id)))

    return {
        "status": "success",
        "stats": {
            "total_courses": courses_count or 0,
            "total_folders": folders_count or 0,
            "total_videos": videos_count or 0,
            "total_users": users_count or 0,
            "total_licenses": licenses_count or 0,
        },
    }


@router.get("/my-courses", status_code=status.HTTP_200_OK)
async def get_my_courses(db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Course))
    courses = query.scalars().all()
    result = []

    for c in courses:
        result.append({"id": c.id, "title": c.title})

    return {"courses": result}


@router.get("/course-content/{course_id}", status_code=status.HTTP_200_OK)
async def get_course_content(course_id: int, db: AsyncSession = Depends(get_db)):
    query = await db.execute(
        select(CourseNode)
        .where(CourseNode.course_id == course_id)
        .options(selectinload(CourseNode.vault_item))  # اصلاح شد
        .order_by(CourseNode.sort_order)
    )
    nodes = query.scalars().all()

    if not nodes:
        return {"sections": []}

    node_dict = {}
    for node in nodes:
        node_data = {
            "id": node.id,
            "parent_id": node.parent_id,
            "item_type": node.item_type,
            "title": node.title,
            "sort_order": node.sort_order,
            "duration": node.duration,
            "children": [],
        }

        if node.vault_item:  # اصلاح شد
            node_data["vault"] = {
                "uuid": node.vault_item.uuid,
                "download_url": node.vault_item.download_url,
            }
        else:
            node_data["vault"] = None

        node_dict[node.id] = node_data

    tree = []
    for node_id, node_data in node_dict.items():
        parent_id = node_data["parent_id"]
        if parent_id is None:
            tree.append(node_data)
        else:
            if parent_id in node_dict:
                node_dict[parent_id]["children"].append(node_data)

    return {"sections": tree}
