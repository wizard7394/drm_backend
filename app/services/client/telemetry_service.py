import os
import json
import logging
import aiofiles
from datetime import datetime, timezone
from app.schemas.client.telemetry import TelemetryBatch

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger(__name__)


class ClientTelemetryService:
    MAX_PAYLOAD_SIZE = 2048

    @staticmethod
    async def process_telemetry_batch(identifier: str, batch: TelemetryBatch):
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_filename = os.path.join(LOG_DIR, f"telemetry_{current_date}.jsonl")

        log_entries = []
        timestamp = datetime.now(timezone.utc).isoformat()

        for event in batch.events:
            payload_str = json.dumps(event.data) if event.data else "{}"

            if (
                len(payload_str.encode("utf-8"))
                > ClientTelemetryService.MAX_PAYLOAD_SIZE
            ):
                logger.warning(
                    f"Oversized telemetry payload from {identifier}. Truncating data."
                )
                payload_str = '{"error": "payload_truncated_due_to_size_limit"}'

            log_entries.append(
                json.dumps(
                    {
                        "timestamp": timestamp,
                        "identifier": identifier,
                        "event_type": event.type,
                        "video_id": event.video,
                        "client_time": event.time,
                        "payload": json.loads(payload_str),
                    }
                )
            )

        if not log_entries:
            return

        try:
            async with aiofiles.open(log_filename, mode="a", encoding="utf-8") as file:
                await file.write("\n".join(log_entries) + "\n")
        except IOError as e:
            logger.error(f"Telemetry async write error for {identifier}: {e}")
