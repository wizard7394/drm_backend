import json
import os
from datetime import datetime, timezone
from app.schemas.client.telemetry import TelemetryBatch

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


class TelemetryService:
    @staticmethod
    def process_telemetry_batch(identifier: str, batch: TelemetryBatch):
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_filename = os.path.join(LOG_DIR, f"telemetry_{current_date}.jsonl")

        log_entries = []
        timestamp = datetime.now(timezone.utc).isoformat()

        for event in batch.events:
            log_entries.append(
                json.dumps(
                    {
                        "timestamp": timestamp,
                        "identifier": identifier,
                        "event_type": event.type,
                        "video_id": event.video,
                        "client_time": event.time,
                        "payload": event.data,
                    }
                )
            )

        try:
            with open(log_filename, "a", encoding="utf-8") as file:
                file.write("\n".join(log_entries) + "\n")
        except IOError as e:
            print(f"Telemetry write error for {identifier}: {e}")
