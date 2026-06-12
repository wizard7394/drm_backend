from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.api.dependencies import get_db
from app.models.course import Course, CourseNode

router = APIRouter()


class CreateCourseRequest(BaseModel):
    title: str
    watermark_text: Optional[str] = None
    watermark_color: Optional[str] = None


class CreateNodeRequest(BaseModel):
    course_id: int
    parent_id: Optional[int] = None
    item_type: str
    title: str
    sort_order: int = 1
    video_url: Optional[str] = None
    duration: Optional[int] = None


class UpdateNodeRequest(BaseModel):
    title: str
    sort_order: int
    video_url: Optional[str] = None
    duration: Optional[int] = None


class KeySyncPayload(BaseModel):
    video_id: int
    aes_key: str
    aes_iv: str


@router.post("/course", status_code=status.HTTP_201_CREATED)
async def create_course(
    request: CreateCourseRequest, db: AsyncSession = Depends(get_db)
):
    new_course = Course(
        title=request.title,
        watermark_text=request.watermark_text,
        watermark_color=request.watermark_color,
    )
    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)
    return {"status": "success", "course_id": new_course.id}


@router.delete("/course/{course_id}", status_code=status.HTTP_200_OK)
async def delete_course(course_id: int, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Course).where(Course.id == course_id))
    course = query.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    await db.delete(course)
    await db.commit()
    return {"status": "success", "message": "Course deleted permanently."}


@router.get("/courses", status_code=status.HTTP_200_OK)
async def get_all_courses(db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Course).order_by(Course.id.desc()))
    courses = query.scalars().all()
    result = []
    for course in courses:
        result.append(
            {
                "id": course.id,
                "title": course.title,
                "watermark_text": course.watermark_text,
                "is_active": course.is_active,
            }
        )
    return {"status": "success", "courses": result}


@router.post("/node", status_code=status.HTTP_201_CREATED)
async def create_node(request: CreateNodeRequest, db: AsyncSession = Depends(get_db)):
    new_node = CourseNode(
        course_id=request.course_id,
        parent_id=request.parent_id,
        item_type=request.item_type,
        title=request.title,
        sort_order=request.sort_order,
        video_url=request.video_url,
        duration=request.duration,
    )
    db.add(new_node)
    await db.commit()
    return {"status": "success"}


@router.put("/node/{node_id}", status_code=status.HTTP_200_OK)
async def update_node(
    node_id: int, request: UpdateNodeRequest, db: AsyncSession = Depends(get_db)
):
    query = await db.execute(select(CourseNode).where(CourseNode.id == node_id))
    node = query.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    node.title = request.title
    node.sort_order = request.sort_order
    if node.item_type == "video":
        node.video_url = request.video_url
        node.duration = request.duration

    await db.commit()
    return {"status": "success"}


@router.delete("/node/{node_id}", status_code=status.HTTP_200_OK)
async def delete_node(node_id: int, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(CourseNode).where(CourseNode.id == node_id))
    node = query.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    await db.delete(node)
    await db.commit()
    return {"status": "success"}


@router.get("/course/{course_id}", status_code=status.HTTP_200_OK)
async def get_course_tree(course_id: int, db: AsyncSession = Depends(get_db)):
    course_query = await db.execute(select(Course).where(Course.id == course_id))
    course = course_query.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    nodes_query = await db.execute(
        select(CourseNode)
        .where(CourseNode.course_id == course_id)
        .order_by(CourseNode.sort_order)
    )
    all_nodes = nodes_query.scalars().all()

    nodes_dict = {}
    for node in all_nodes:
        nodes_dict[node.id] = {
            "id": node.id,
            "parent_id": node.parent_id,
            "item_type": node.item_type,
            "title": node.title,
            "sort_order": node.sort_order,
            "video_url": node.video_url,
            "duration": node.duration,
            "is_encrypted": bool(node.aes_key and node.aes_iv),
            "children": [],
        }

    tree = []
    for node_id, node_data in nodes_dict.items():
        if node_data["parent_id"] is None:
            tree.append(node_data)
        else:
            parent_id = node_data["parent_id"]
            if parent_id in nodes_dict:
                nodes_dict[parent_id]["children"].append(node_data)
            else:
                tree.append(node_data)

    return {
        "status": "success",
        "course": {
            "id": course.id,
            "title": course.title,
        },
        "tree": tree,
    }


@router.post("/keys/sync", status_code=status.HTTP_200_OK)
async def sync_video_keys(payload: KeySyncPayload, db: AsyncSession = Depends(get_db)):
    query = await db.execute(
        select(CourseNode).where(
            CourseNode.id == payload.video_id, CourseNode.item_type == "video"
        )
    )
    db_video = query.scalars().first()

    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found")

    db_video.aes_key = payload.aes_key
    db_video.aes_iv = payload.aes_iv

    try:
        await db.commit()
        return {"status": "success", "message": "Encryption keys synced securely."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
