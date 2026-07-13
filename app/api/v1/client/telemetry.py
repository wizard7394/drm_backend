from fastapi import APIRouter, BackgroundTasks, Depends, status
from app.models.user import User
from app.schemas.telemetry import TelemetryBatch
from app.services.telemetry_service import TelemetryService
from app.api.v1.client.dependencies import get_current_user

router = APIRouter()


@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
async def submit_telemetry_batch(
    payload: TelemetryBatch,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    background_tasks.add_task(
        TelemetryService.process_telemetry_batch, current_user.mobile, payload
    )
    return {"status": "processing", "message": "Telemetry queued."}
