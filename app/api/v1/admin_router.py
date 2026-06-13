from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List
from app.api.dependencies import get_db
from app.models.course import Course, CourseNode
from app.models.vault import VideoVault

router = APIRouter()


class AutoBuildRequest(BaseModel):
    batch_name: str


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
    attachment_url: Optional[str] = None
    vault_id: Optional[int] = None


class UpdateNodeRequest(BaseModel):
    title: str
    sort_order: int
    video_url: Optional[str] = None
    duration: Optional[int] = None
    attachment_url: Optional[str] = None
    vault_id: Optional[int] = None


class VaultItemPayload(BaseModel):
    uuid: str
    file_hash: str
    aes_key: str
    aes_iv: str
    original_filename: Optional[str] = None


class VaultBulkUploadRequest(BaseModel):
    course_id: int
    batch_name: str
    items: List[VaultItemPayload]


class UpdateVaultUrlRequest(BaseModel):
    download_url: str


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
    return {"status": "success"}


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
    if request.vault_id:
        v_query = await db.execute(
            select(VideoVault).where(VideoVault.id == request.vault_id)
        )
        v_item = v_query.scalars().first()
        if v_item:
            v_item.status = "used"

    new_node = CourseNode(
        course_id=request.course_id,
        parent_id=request.parent_id,
        item_type=request.item_type,
        title=request.title,
        sort_order=request.sort_order,
        video_url=request.video_url,
        duration=request.duration,
        attachment_url=request.attachment_url,
        vault_id=request.vault_id,
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

    if node.item_type == "video" and request.vault_id != node.vault_id:
        if node.vault_id:
            old_q = await db.execute(
                select(VideoVault).where(VideoVault.id == node.vault_id)
            )
            old_v = old_q.scalars().first()
            if old_v:
                old_v.status = "orphaned"
        if request.vault_id:
            new_q = await db.execute(
                select(VideoVault).where(VideoVault.id == request.vault_id)
            )
            new_v = new_q.scalars().first()
            if new_v:
                new_v.status = "used"

    node.title = request.title
    node.sort_order = request.sort_order
    if node.item_type == "video":
        node.video_url = request.video_url
        node.duration = request.duration
        node.attachment_url = request.attachment_url
        node.vault_id = request.vault_id

    await db.commit()
    return {"status": "success"}


@router.delete("/node/{node_id}", status_code=status.HTTP_200_OK)
async def delete_node(node_id: int, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(CourseNode).where(CourseNode.id == node_id))
    node = query.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if node.vault_id:
        v_q = await db.execute(select(VideoVault).where(VideoVault.id == node.vault_id))
        v_item = v_q.scalars().first()
        if v_item:
            v_item.status = "orphaned"

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
        .options(selectinload(CourseNode.vault_item))
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
            "attachment_url": node.attachment_url,
            "vault_id": node.vault_id,
            "is_encrypted": bool(node.vault_id),
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
        "course": {"id": course.id, "title": course.title},
        "tree": tree,
    }


@router.post("/vault/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_upload_vault(
    request: VaultBulkUploadRequest, db: AsyncSession = Depends(get_db)
):
    for item in request.items:
        new_vault = VideoVault(
            course_id=request.course_id,
            batch_name=request.batch_name,
            uuid=item.uuid,
            original_filename=item.original_filename,
            file_hash=item.file_hash,
            aes_key=item.aes_key,
            aes_iv=item.aes_iv,
        )
        db.add(new_vault)
    await db.commit()
    return {"status": "success", "inserted": len(request.items)}


@router.get("/vault/{course_id}", status_code=status.HTTP_200_OK)
async def get_vault_items(
    course_id: int, status_filter: str = "unused", db: AsyncSession = Depends(get_db)
):
    query = await db.execute(
        select(VideoVault).where(
            VideoVault.course_id == course_id, VideoVault.status == status_filter
        )
    )
    items = query.scalars().all()
    result = []
    for item in items:
        result.append(
            {
                "id": item.id,
                "batch_name": item.batch_name,
                "uuid": item.uuid,
                "original_filename": item.original_filename,
                "file_hash": item.file_hash,
                "download_url": item.download_url,
                "status": item.status,
                "created_at": item.created_at,
            }
        )
    return {"status": "success", "vault_items": result}


@router.put("/vault/{vault_id}/url", status_code=status.HTTP_200_OK)
async def update_vault_url(
    vault_id: int, request: UpdateVaultUrlRequest, db: AsyncSession = Depends(get_db)
):
    query = await db.execute(select(VideoVault).where(VideoVault.id == vault_id))
    v_item = query.scalars().first()
    if not v_item:
        raise HTTPException(status_code=404, detail="Vault item not found")
    v_item.download_url = request.download_url
    await db.commit()
    return {"status": "success"}


@router.delete("/vault/{vault_id}", status_code=status.HTTP_200_OK)
async def delete_vault_item(vault_id: int, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(VideoVault).where(VideoVault.id == vault_id))
    v_item = query.scalars().first()
    if not v_item:
        raise HTTPException(status_code=404, detail="Vault item not found")
    await db.delete(v_item)
    await db.commit()
    return {"status": "success"}


@router.post("/vault/{course_id}/auto-build", status_code=status.HTTP_200_OK)
async def auto_build_course_tree(
    course_id: int, request: AutoBuildRequest, db: AsyncSession = Depends(get_db)
):
    query = await db.execute(
        select(VideoVault)
        .where(
            VideoVault.course_id == course_id,
            VideoVault.batch_name == request.batch_name,
            VideoVault.status == "unused",
        )
        .order_by(VideoVault.original_filename)
    )
    vault_items = query.scalars().all()

    if not vault_items:
        raise HTTPException(
            status_code=400, detail="No unused items found for this batch."
        )

    folder_cache = {}

    for item in vault_items:
        if not item.original_filename:
            continue

        parts = item.original_filename.split("/")
        parent_id = None
        current_path = ""

        for i in range(len(parts) - 1):
            folder_name = parts[i]
            current_path = (
                f"{current_path}/{folder_name}" if current_path else folder_name
            )

            if current_path in folder_cache:
                parent_id = folder_cache[current_path]
            else:
                node_q = await db.execute(
                    select(CourseNode).where(
                        CourseNode.course_id == course_id,
                        CourseNode.parent_id == parent_id,
                        CourseNode.title == folder_name,
                        CourseNode.item_type == "folder",
                    )
                )
                existing_node = node_q.scalars().first()

                if existing_node:
                    parent_id = existing_node.id
                    folder_cache[current_path] = parent_id
                else:
                    new_folder = CourseNode(
                        course_id=course_id,
                        parent_id=parent_id,
                        item_type="folder",
                        title=folder_name,
                        sort_order=1,
                    )
                    db.add(new_folder)
                    await db.flush()
                    parent_id = new_folder.id
                    folder_cache[current_path] = parent_id

        file_name = parts[-1]
        title = file_name.rsplit(".", 1)[0] if "." in file_name else file_name

        new_video = CourseNode(
            course_id=course_id,
            parent_id=parent_id,
            item_type="video",
            title=title,
            sort_order=1,
            vault_id=item.id,
        )
        db.add(new_video)
        item.status = "used"

    await db.commit()
    return {"status": "success", "processed_items": len(vault_items)}
