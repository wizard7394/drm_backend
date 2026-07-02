from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy import update, select, func
import os
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import (
    get_db,
    get_vault_db,
    get_current_user,
    get_current_admin,
)
from app.models.user import User
from app.models.admin import Admin
from app.models.course import Course, CourseNode
from app.models.vault import VaultItem
from pydantic import BaseModel
from app.services.course_service import CourseService
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    NodeCreate,
    NodeUpdate,
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
    query = await vault_db.execute(select(Course).where(Course.id == course_id))
    course = query.scalars().first()

    if not course:
        return {"status": "error", "message": "Course not found"}

    if data.title is not None:
        course.title = data.title
    if data.is_active is not None:
        course.is_active = data.is_active
    if data.base_stream_url is not None:
        course.base_stream_url = data.base_stream_url

    await vault_db.commit()
    return {"status": "success"}


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
    from app.models.course import CourseNode
    from sqlalchemy import select

    query = await vault_db.execute(select(CourseNode).where(CourseNode.id == node_id))
    node = query.scalars().first()
    if not node:
        return {"status": "error", "message": "Node not found"}

    if data.title is not None:
        node.title = data.title
    if data.sort_order is not None:
        node.sort_order = data.sort_order
    if data.duration is not None:
        node.duration = data.duration
    if data.video_url is not None:
        node.video_url = data.video_url
    if data.vault_id is not None:
        node.vault_id = data.vault_id
    if data.attachments is not None:
        node.attachments = data.attachments

    await vault_db.commit()
    return {"status": "success"}


@router.delete("/admin/node/delete/{node_id}")
async def delete_course_node(
    node_id: int,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return await CourseService.delete_node(node_id, vault_db)


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


class NodeReorderItem(BaseModel):
    node_id: int
    sort_order: int


@router.post("/admin/node/reorder")
async def reorder_nodes(
    items: List[NodeReorderItem],
    vault_db: AsyncSession = Depends(get_vault_db),
    admin: Admin = Depends(get_current_admin),
):
    for item in items:
        await vault_db.execute(
            update(CourseNode)
            .where(CourseNode.id == item.node_id)
            .values(sort_order=item.sort_order)
        )
    await vault_db.commit()
    return {"status": "success"}


@router.post("/admin/vault/bulk")
async def inject_keys(
    data: dict,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):
    from sqlalchemy import or_

    batch_name = data.get("batch_name")
    items = data.get("items", [])

    for item in items:
        uuid_val = item.get("uuid")
        orig_name = item.get("original_filename")

        stmt = select(VaultItem).where(
            or_(
                VaultItem.uuid == uuid_val,
                (VaultItem.batch_name == batch_name)
                & (VaultItem.original_filename == orig_name),
            )
        )
        existing = await vault_db.execute(stmt)
        vault_record = existing.scalars().first()

        decryption_key = item.get(
            "encryption_key", item.get("decryption_key", item.get("aes_key"))
        )

        if vault_record:
            vault_record.batch_name = batch_name
            vault_record.original_filename = orig_name
            vault_record.file_hash = item.get("file_hash")
            vault_record.decryption_key = decryption_key
            vault_record.uuid = uuid_val
            vault_record.duration = item.get("duration")
        else:
            new_vault = VaultItem(
                uuid=uuid_val,
                batch_name=batch_name,
                original_filename=orig_name,
                file_hash=item.get("file_hash"),
                decryption_key=decryption_key,
                duration=item.get("duration"),
                download_url=item.get("download_url", ""),
            )
            vault_db.add(new_vault)

    await vault_db.commit()
    return {"status": "success"}


@router.post("/admin/vault/trigger-autobuild/{course_id}")
async def trigger_autobuild(
    course_id: int,
    payload: dict,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_admin: Admin = Depends(get_current_admin),
):

    batch_name = payload.get("batch_name")
    if not batch_name:
        return {"status": "error", "message": "Missing batch_name"}

    course_query = await vault_db.execute(select(Course).where(Course.id == course_id))
    course = course_query.scalars().first()

    base_url = (
        course.base_stream_url
        if course and course.base_stream_url
        else "https://cdn.nabegheha.com/download"
    )

    vault_query = await vault_db.execute(
        select(VaultItem).where(VaultItem.batch_name == batch_name)
    )
    vault_items = vault_query.scalars().all()

    nodes_query = await vault_db.execute(
        select(CourseNode).where(CourseNode.course_id == course_id)
    )
    existing_nodes = nodes_query.scalars().all()

    existing_vault_ids = [n.vault_id for n in existing_nodes if n.vault_id is not None]

    for item in vault_items:
        if item.id not in existing_vault_ids:
            current_parent_id = None
            file_path = item.original_filename or item.uuid
            parts = file_path.split("/")
            folders = parts[:-1]

            # حذف اتوماتیک پسوند از اسم فایل برای تمیزی پنل
            filename_with_ext = parts[-1]
            clean_title, _ = os.path.splitext(filename_with_ext)

            for folder_name in folders:
                stmt = select(CourseNode).where(
                    CourseNode.course_id == course_id,
                    CourseNode.item_type == "folder",
                    CourseNode.title == folder_name,
                )
                if current_parent_id is None:
                    stmt = stmt.where(CourseNode.parent_id.is_(None))
                else:
                    stmt = stmt.where(CourseNode.parent_id == current_parent_id)

                folder_query = await vault_db.execute(stmt)
                folder = folder_query.scalars().first()

                if folder:
                    current_parent_id = folder.id
                else:
                    sort_stmt = select(func.max(CourseNode.sort_order)).where(
                        CourseNode.course_id == course_id
                    )
                    if current_parent_id is None:
                        sort_stmt = sort_stmt.where(CourseNode.parent_id.is_(None))
                    else:
                        sort_stmt = sort_stmt.where(
                            CourseNode.parent_id == current_parent_id
                        )

                    max_sort_query = await vault_db.execute(sort_stmt)
                    max_sort = max_sort_query.scalar() or 0

                    new_folder = CourseNode(
                        course_id=course_id,
                        parent_id=current_parent_id,
                        item_type="folder",
                        title=folder_name,
                        sort_order=max_sort + 1,
                    )
                    vault_db.add(new_folder)
                    await vault_db.flush()
                    current_parent_id = new_folder.id

            sort_stmt = select(func.max(CourseNode.sort_order)).where(
                CourseNode.course_id == course_id
            )
            if current_parent_id is None:
                sort_stmt = sort_stmt.where(CourseNode.parent_id.is_(None))
            else:
                sort_stmt = sort_stmt.where(CourseNode.parent_id == current_parent_id)

            max_sort_query = await vault_db.execute(sort_stmt)
            max_sort = max_sort_query.scalar() or 0

            video_url = f"{base_url.rstrip('/')}/{item.uuid}.enc"

            new_video = CourseNode(
                course_id=course_id,
                parent_id=current_parent_id,
                item_type="video",
                title=clean_title,
                sort_order=max_sort + 1,
                video_url=video_url,
                duration=item.duration,
                vault_id=item.id,
            )
            vault_db.add(new_video)
            await vault_db.flush()

    await vault_db.commit()
    return {"status": "success"}


@router.post("/watched/{vault_uuid}")
async def mark_video_watched(
    vault_uuid: str,
    vault_db: AsyncSession = Depends(get_vault_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.course import WatchedVideo
    from sqlalchemy import select

    stmt = select(WatchedVideo).where(
        WatchedVideo.user_id == current_user.id, WatchedVideo.vault_uuid == vault_uuid
    )
    result = await vault_db.execute(stmt)
    existing = result.scalars().first()

    if not existing:
        new_watched = WatchedVideo(user_id=current_user.id, vault_uuid=vault_uuid)
        vault_db.add(new_watched)
        await vault_db.commit()

    return {"status": "success"}


@router.get("/watched")
async def get_watched_videos(
    vault_db: AsyncSession = Depends(get_vault_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.course import WatchedVideo
    from sqlalchemy import select

    stmt = select(WatchedVideo.vault_uuid).where(
        WatchedVideo.user_id == current_user.id
    )
    result = await vault_db.execute(stmt)
    watched_uuids = result.scalars().all()

    return {"status": "success", "watched_uuids": watched_uuids}
