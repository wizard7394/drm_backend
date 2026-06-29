from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import (
    get_db,
    get_vault_db,
    get_current_user,
    get_current_admin,
)
from app.models.user import User
from app.models.admin import Admin
from pydantic import BaseModel
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
    vault_db: AsyncSession = Depends(get_vault_db),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.get_all_courses_admin(vault_db, db)


@router.get("/admin/export")
async def export_vault_data_api(
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.export_vault_data(vault_db)


@router.post("/admin/import")
async def import_vault_data_api(
    data: dict,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.import_vault_data(data, vault_db)


@router.post("/admin/create")
async def create_new_course(
    data: CourseCreate,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.create_course(data, vault_db)


@router.put("/admin/update/{course_id}")
async def update_existing_course(
    course_id: int,
    data: CourseUpdate,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.update_course(course_id, data, vault_db)


@router.delete("/admin/delete/{course_id}")
async def delete_existing_course(
    course_id: int,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.delete_course(course_id, vault_db)


@router.post("/admin/node/create")
async def create_course_node(
    data: NodeCreate,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.create_node(data, vault_db)


@router.put("/admin/node/update/{node_id}")
async def update_course_node(
    node_id: int,
    data: NodeUpdate,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.update_node(node_id, data, vault_db)


@router.delete("/admin/node/delete/{node_id}")
async def delete_course_node(
    node_id: int,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.delete_node(node_id, vault_db)


@router.post("/admin/autobuild")
async def auto_build_course_nodes(
    data: AutoBuildRequest,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.auto_build_course(data, vault_db)


@router.get("/admin/view/{course_id}")
async def get_course_tree_for_admin(
    course_id: int,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.get_course_tree_admin(course_id, vault_db)


@router.get("/view/{course_id}")
async def get_course_details(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    vault_db: AsyncSession = Depends(get_vault_db),
    current_user: User = Depends(get_current_user),
):
    return await CourseService.get_course_details(course_id, current_user, db, vault_db)


class CourseUpdateRequest(BaseModel):
    title: str
    is_active: bool


@router.put("/admin/update/{course_id}")
async def update_course(
    course_id: int,
    data: CourseUpdateRequest,
    vault_db: AsyncSession = Depends(get_vault_db),
    admin: Admin = Depends(get_current_admin),
):
    from app.models.course import Course
    from sqlalchemy import select

    query = await vault_db.execute(select(Course).where(Course.id == course_id))
    course = query.scalars().first()

    if not course:
        return {"status": "error", "message": "Course not found"}

    course.title = data.title
    course.is_active = data.is_active
    await vault_db.commit()

    return {"status": "success"}


class NodeReorderItem(BaseModel):
    node_id: int
    sort_order: int


@router.post("/admin/node/reorder")
async def reorder_nodes(
    items: List[NodeReorderItem],
    vault_db: AsyncSession = Depends(get_vault_db),
    admin: Admin = Depends(get_current_admin),
):
    from app.models.course import CourseNode

    for item in items:
        await vault_db.execute(
            update(CourseNode)
            .where(CourseNode.id == item.node_id)
            .values(sort_order=item.sort_order)
        )
    await vault_db.commit()
    return {"status": "success"}
