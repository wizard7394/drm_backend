from fastapi import APIRouter, BackgroundTasks, status
from sqlalchemy import select
from app.schemas.telemetry import HeatmapPayload
from app.models.telemetry import VideoHeatmap
from app.models.license import License
from app.core.database import AsyncSessionLocal

router = APIRouter()

async def process_heatmap_batch(payload: HeatmapPayload):
    async with AsyncSessionLocal() as db:
        license_query = await db.execute(select(License).where(License.license_key == payload.license_key))
        db_license = license_query.scalars().first()

        if not db_license:
            return

        new_logs = [
            VideoHeatmap(
                video_id=payload.video_id,
                license_id=db_license.id,
                watched_second=sec
            )
            for sec in payload.watched_seconds
        ]

        db.add_all(new_logs)
        await db.commit()

@router.post("/heatmap", status_code=status.HTTP_202_ACCEPTED)
async def submit_heatmap(payload: HeatmapPayload, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_heatmap_batch, payload)
    return {"status": "processing", "message": "Telemetry data queued successfully."}