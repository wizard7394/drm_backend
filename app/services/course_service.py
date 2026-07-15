import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from app.models.course import Course, CourseNode, WatchedVideo
from app.models.license import License
from app.models.user import User
from app.models.vault import VaultItem
from app.core.errors import AppErrors
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    NodeCreate,
    NodeUpdate,
    VaultBulkInjectRequest,
    TriggerAutobuildRequest,
)


class CourseService:
    @staticmethod
    async def get_user_courses(
        current_user: User, db: AsyncSession, vault_db: AsyncSession
    ):
        stmt = select(License.course_id).where(
            License.user_id == current_user.id, License.is_active
        )
        license_result = await db.execute(stmt)
        course_ids = license_result.scalars().all()

        if not course_ids:
            return {"status": "success", "courses": []}

        course_stmt = select(Course).where(Course.id.in_(course_ids), Course.is_active)
        course_result = await vault_db.execute(course_stmt)
        courses = course_result.scalars().all()

        course_list = [
            {"id": c.id, "title": c.title, "is_active": bool(c.is_active)}
            for c in courses
        ]
        return {"status": "success", "courses": course_list}

    @staticmethod
    async def get_course_details(
        course_id: int,
        current_user: User,
        main_db: AsyncSession,
        vault_db: AsyncSession,
    ):
        license_query = await main_db.execute(
            select(License).where(
                License.user_id == current_user.id,
                License.course_id == course_id,
                License.is_active,
            )
        )
        db_license = license_query.scalars().first()

        if not db_license:
            raise AppErrors.COURSE_ACCESS_DENIED

        if db_license.expires_at:
            expire_time = db_license.expires_at
            if expire_time.tzinfo is None:
                expire_time = expire_time.replace(tzinfo=timezone.utc)
            if expire_time < datetime.now(timezone.utc):
                raise AppErrors.LICENSE_EXPIRED

        course_query = await vault_db.execute(
            select(Course).where(Course.id == course_id, Course.is_active)
        )
        course_obj = course_query.scalars().first()

        if not course_obj:
            raise AppErrors.COURSE_NOT_FOUND

        nodes_query = await vault_db.execute(
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
                "attachments": node.attachments,
                "vault": {
                    "uuid": node.vault_item.uuid,
                    "file_hash": node.vault_item.file_hash,
                    "download_url": node.vault_item.download_url,
                }
                if getattr(node, "vault_item", None)
                else None,
                "children": [],
            }

        tree = []
        for node_id, node_data in nodes_dict.items():
            parent_id = node_data["parent_id"]
            if parent_id is None:
                tree.append(node_data)
            else:
                if parent_id in nodes_dict:
                    nodes_dict[parent_id]["children"].append(node_data)
                else:
                    tree.append(node_data)

        return {
            "id": course_obj.id,
            "title": course_obj.title,
            "watermark_text": course_obj.watermark_text,
            "watermark_color": course_obj.watermark_color,
            "sections": tree,
        }

    @staticmethod
    async def mark_video_watched(
        vault_uuid: str, current_user: User, vault_db: AsyncSession
    ):
        stmt = select(WatchedVideo).where(
            WatchedVideo.user_id == current_user.id,
            WatchedVideo.vault_uuid == vault_uuid,
        )
        result = await vault_db.execute(stmt)
        existing = result.scalars().first()

        if not existing:
            new_watched = WatchedVideo(user_id=current_user.id, vault_uuid=vault_uuid)
            vault_db.add(new_watched)
            await vault_db.commit()

        return {"status": "success"}

    @staticmethod
    async def get_watched_videos(current_user: User, vault_db: AsyncSession):
        stmt = select(WatchedVideo.vault_uuid).where(
            WatchedVideo.user_id == current_user.id
        )
        result = await vault_db.execute(stmt)
        watched_uuids = result.scalars().all()

        return {"status": "success", "watched_uuids": watched_uuids}

    @staticmethod
    async def get_all_courses_admin(vault_db: AsyncSession, main_db: AsyncSession):
        courses_query = await vault_db.execute(
            select(Course).order_by(Course.id.desc())
        )
        courses = courses_query.scalars().all()

        result = []
        for c in courses:
            students_query = await main_db.execute(
                select(func.count(License.id)).where(License.course_id == c.id)
            )
            students_count = students_query.scalar() or 0

            videos_query = await vault_db.execute(
                select(func.count(CourseNode.id)).where(
                    CourseNode.course_id == c.id, CourseNode.item_type == "video"
                )
            )
            videos_count = videos_query.scalar() or 0

            result.append(
                {
                    "id": c.id,
                    "title": c.title,
                    "is_active": c.is_active,
                    "total_students": students_count,
                    "total_videos": videos_count,
                }
            )
        return result

    @staticmethod
    async def get_course_tree_admin(course_id: int, vault_db: AsyncSession):
        course_query = await vault_db.execute(
            select(Course).where(Course.id == course_id)
        )
        course_obj = course_query.scalars().first()

        if not course_obj:
            raise AppErrors.COURSE_NOT_FOUND

        nodes_query = await vault_db.execute(
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
                "attachments": node.attachments,
                "vault": {
                    "uuid": node.vault_item.uuid,
                    "file_hash": node.vault_item.file_hash,
                    "download_url": node.vault_item.download_url,
                }
                if getattr(node, "vault_item", None)
                else None,
                "children": [],
            }

        tree = []
        for node_id, node_data in nodes_dict.items():
            parent_id = node_data["parent_id"]
            if parent_id is None:
                tree.append(node_data)
            else:
                if parent_id in nodes_dict:
                    nodes_dict[parent_id]["children"].append(node_data)
                else:
                    tree.append(node_data)

        return {
            "id": course_obj.id,
            "title": course_obj.title,
            "watermark_text": course_obj.watermark_text,
            "watermark_color": course_obj.watermark_color,
            "tree": tree,
        }

    @staticmethod
    async def create_course(data: CourseCreate, vault_db: AsyncSession):
        new_course = Course(
            title=data.title,
            watermark_text=data.watermark_text,
            watermark_color=data.watermark_color,
            is_active=data.is_active,
        )
        vault_db.add(new_course)
        await vault_db.commit()
        await vault_db.refresh(new_course)
        return new_course

    @staticmethod
    async def update_course(course_id: int, data: CourseUpdate, vault_db: AsyncSession):
        course_query = await vault_db.execute(
            select(Course).where(Course.id == course_id)
        )
        course = course_query.scalars().first()

        if not course:
            raise AppErrors.COURSE_NOT_FOUND

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(course, key, value)

        await vault_db.commit()
        await vault_db.refresh(course)
        return course

    @staticmethod
    async def delete_course(course_id: int, vault_db: AsyncSession):
        course_query = await vault_db.execute(
            select(Course).where(Course.id == course_id)
        )
        course = course_query.scalars().first()
        if not course:
            raise AppErrors.COURSE_NOT_FOUND

        await vault_db.delete(course)
        await vault_db.commit()
        return {"status": "success", "message": "Course deleted permanently"}

    @staticmethod
    async def create_node(data: NodeCreate, vault_db: AsyncSession):
        new_node = CourseNode(
            course_id=data.course_id,
            parent_id=data.parent_id,
            item_type=data.item_type,
            title=data.title,
            sort_order=data.sort_order,
            video_url=data.video_url,
            duration=data.duration,
            attachments=data.attachments,
            vault_id=data.vault_id,
        )
        vault_db.add(new_node)
        await vault_db.commit()
        await vault_db.refresh(new_node)
        return {"status": "success", "node_id": new_node.id}

    @staticmethod
    async def update_node(node_id: int, data: NodeUpdate, vault_db: AsyncSession):
        node_query = await vault_db.execute(
            select(CourseNode).where(CourseNode.id == node_id)
        )
        node = node_query.scalars().first()
        if not node:
            raise Exception("Node missing from database")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(node, key, value)

        await vault_db.commit()
        return {"status": "success"}

    @staticmethod
    async def delete_node(node_id: int, vault_db: AsyncSession):
        node_query = await vault_db.execute(
            select(CourseNode).where(CourseNode.id == node_id)
        )
        node = node_query.scalars().first()
        if not node:
            raise Exception("Node missing from database")

        await vault_db.delete(node)
        await vault_db.commit()
        return {"status": "success"}

    @staticmethod
    async def inject_vault_keys_bulk(
        data: VaultBulkInjectRequest, vault_db: AsyncSession
    ):
        batch_name = data.batch_name

        for item in data.items:
            stmt = select(VaultItem).where(
                or_(
                    VaultItem.uuid == item.uuid,
                    (VaultItem.batch_name == batch_name)
                    & (VaultItem.original_filename == item.original_filename),
                )
            )
            existing = await vault_db.execute(stmt)
            vault_record = existing.scalars().first()

            dec_key = (
                getattr(item, "encryption_key", None)
                or getattr(item, "decryption_key", None)
                or getattr(item, "aes_key", None)
            )
            aes_iv_val = getattr(item, "aes_iv", None) or getattr(item, "iv", None)

            if vault_record:
                vault_record.batch_name = batch_name
                vault_record.original_filename = item.original_filename
                vault_record.file_hash = item.file_hash
                vault_record.decryption_key = dec_key
                vault_record.aes_iv = aes_iv_val
                vault_record.uuid = item.uuid
                vault_record.duration = item.duration
            else:
                new_vault = VaultItem(
                    uuid=item.uuid,
                    batch_name=batch_name,
                    original_filename=item.original_filename,
                    file_hash=item.file_hash,
                    decryption_key=dec_key,
                    aes_iv=aes_iv_val,
                    duration=item.duration,
                    download_url=getattr(item, "download_url", ""),
                )
                vault_db.add(new_vault)

        await vault_db.commit()
        return {"status": "success"}

    @staticmethod
    async def auto_build_course_tree(
        course_id: int, payload: TriggerAutobuildRequest, vault_db: AsyncSession
    ):
        batch_name = payload.batch_name
        cdn_base_url = os.getenv("CDN_BASE_URL", "https://cdn.nabegheha.com/download")

        course_query = await vault_db.execute(
            select(Course).where(Course.id == course_id)
        )
        course = course_query.scalars().first()

        if not course:
            course = Course(
                id=course_id,
                title=f"Auto Generated Course {course_id}",
                is_active=True,
            )
            vault_db.add(course)
            await vault_db.flush()

        base_url = getattr(course, "base_stream_url", None) or cdn_base_url

        vault_query = await vault_db.execute(
            select(VaultItem).where(VaultItem.batch_name == batch_name)
        )
        vault_items = vault_query.scalars().all()

        nodes_query = await vault_db.execute(
            select(CourseNode).where(CourseNode.course_id == course_id)
        )
        existing_nodes = nodes_query.scalars().all()
        existing_vault_ids = [
            n.vault_id for n in existing_nodes if n.vault_id is not None
        ]

        for item in vault_items:
            if item.id not in existing_vault_ids:
                current_parent_id = None
                file_path = item.original_filename or item.uuid
                parts = file_path.split("/")
                folders = parts[:-1]
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
                    sort_stmt = sort_stmt.where(
                        CourseNode.parent_id == current_parent_id
                    )

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
