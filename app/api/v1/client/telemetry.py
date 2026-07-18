from fastapi import APIRouter, BackgroundTasks, Depends, status
from app.models.user import User
from app.schemas.client.telemetry import TelemetryBatch
from app.services.client.telemetry_service import ClientTelemetryService
from app.api.v1.client.dependencies import get_current_user

router = APIRouter()


@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
async def submit_telemetry_batch(
    payload: TelemetryBatch,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    identifier = current_user.mobile or current_user.email or str(current_user.id)

    background_tasks.add_task(
        ClientTelemetryService.process_telemetry_batch, identifier, payload
    )
    return {"status": "processing", "message": "Telemetry queued."}
