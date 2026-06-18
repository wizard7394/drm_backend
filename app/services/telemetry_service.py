import json
import os
from datetime import datetime, timezone
from app.schemas.telemetry import TelemetryBatch

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


class TelemetryService:
    @staticmethod
    def process_telemetry_batch(phone_number: str, batch: TelemetryBatch):
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_filename = os.path.join(LOG_DIR, f"telemetry_{current_date}.jsonl")

        try:
            with open(log_filename, "a", encoding="utf-8") as file:
                for event in batch.events:
                    log_entry = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "phone_number": phone_number,
                        "event_type": event.type,
                        "video_id": event.video,
                        "client_time": event.time,
                        "payload": event.data,
                    }
                    file.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"telemetry_write_error_for_phone_{phone_number}: {e}")
