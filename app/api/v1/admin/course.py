from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, get_vault_db
from app.api.v1.admin.dependencies import get_current_admin
from app.models.admin import Admin
from app.models.course import CourseNode
from pydantic import BaseModel
from app.services.course_service import CourseService

from app.schemas.admin.course import (
    CourseCreate,
    CourseUpdate,
    NodeCreate,
    NodeUpdate,
    VaultBulkInjectRequest,
    TriggerAutobuildRequest,
)

router = APIRouter()


@router.get("/list")
async def get_all_courses_for_admin(
    vault_db: AsyncSession = Depends(get_vault_db),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.get_all_courses_admin(vault_db, db)


@router.post("/create")
async def create_new_course(
    data: CourseCreate,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.create_course(data, vault_db)


@router.put("/update/{course_id}")
async def update_existing_course(
    course_id: int,
    data: CourseUpdate,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.update_course(course_id, data, vault_db)


@router.delete("/delete/{course_id}")
async def delete_existing_course(
    course_id: int,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.delete_course(course_id, vault_db)


@router.post("/node/create")
async def create_course_node(
    data: NodeCreate,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.create_node(data, vault_db)


@router.put("/node/update/{node_id}")
async def update_course_node(
    node_id: int,
    data: NodeUpdate,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.update_node(node_id, data, vault_db)


@router.delete("/node/delete/{node_id}")
async def delete_course_node(
    node_id: int,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.delete_node(node_id, vault_db)


@router.get("/view/{course_id}")
async def get_course_tree_for_admin(
    course_id: int,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.get_course_tree_admin(course_id, vault_db)


class NodeReorderItem(BaseModel):
    node_id: int
    sort_order: int


@router.post("/node/reorder")
async def reorder_nodes(
    items: List[NodeReorderItem],
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    for item in items:
        await vault_db.execute(
            update(CourseNode)
            .where(CourseNode.id == item.node_id)
            .values(sort_order=item.sort_order)
        )
    await vault_db.commit()
    return {"status": "success"}


@router.post("/vault/bulk")
async def inject_keys(
    data: VaultBulkInjectRequest,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.inject_vault_keys_bulk(data, vault_db)


@router.post("/vault/trigger-autobuild/{course_id}")
async def trigger_autobuild(
    course_id: int,
    payload: TriggerAutobuildRequest,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.auto_build_course_tree(course_id, payload, vault_db)
