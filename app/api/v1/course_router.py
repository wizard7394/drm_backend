from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.course_service import CourseService
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    NodeCreate,
    NodeUpdate,
    AutoBuildRequest,
)

router = APIRouter()


@router.get("/admin/list")
async def get_all_courses_for_admin(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CourseService.get_all_courses_admin(db)


@router.post("/admin/create")
async def create_new_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CourseService.create_course(data, db)


@router.put("/admin/update/{course_id}")
async def update_existing_course(
    course_id: int,
    data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CourseService.update_course(course_id, data, db)


@router.delete("/admin/delete/{course_id}")
async def delete_existing_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CourseService.delete_course(course_id, db)


@router.post("/admin/node/create")
async def create_course_node(
    data: NodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CourseService.create_node(data, db)


@router.put("/admin/node/update/{node_id}")
async def update_course_node(
    node_id: int,
    data: NodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CourseService.update_node(node_id, data, db)


@router.delete("/admin/node/delete/{node_id}")
async def delete_course_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CourseService.delete_node(node_id, db)


@router.post("/admin/autobuild")
async def auto_build_course_nodes(
    data: AutoBuildRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CourseService.auto_build_course(data, db)


@router.get("/view/{course_id}")  # تغییر از {course_id} به view/{course_id}
async def get_course_details(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CourseService.get_course_details(course_id, current_user, db)
