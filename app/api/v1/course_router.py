from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.api.dependencies import get_db, get_current_device
from app.models.course import Course, CourseNode
from app.models.license import License
from app.models.device import HardwareDevice

router = APIRouter()


@router.get("/{course_id}")
async def get_course_details(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_device: HardwareDevice = Depends(get_current_device),
):
    license_query = await db.execute(
        select(License).where(License.id == current_device.license_id)
    )
    db_license = license_query.scalars().first()

    if not db_license or db_license.course_id != course_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Your license does not cover this course.",
        )

    course_query = await db.execute(
        select(Course).where(Course.id == course_id, Course.is_active)
    )
    course_obj = course_query.scalars().first()

    if not course_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or inactive.",
        )

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
            "duration": node.duration,
            "attachment_url": node.attachment_url,
            "vault": {
                "uuid": node.vault_item.uuid,
                "file_hash": node.vault_item.file_hash,
                "download_url": node.vault_item.download_url,
            }
            if node.vault_item
            else None,
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
        "id": course_obj.id,
        "title": course_obj.title,
        "watermark_text": course_obj.watermark_text,
        "tree": tree,
    }
