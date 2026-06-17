import json
import os
from datetime import datetime, timezone
from app.schemas.telemetry import TelemetryBatch

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
TELEMETRY_FILE = os.path.join(LOG_DIR, "telemetry_events.jsonl")


class TelemetryService:
    @staticmethod
    def process_telemetry_batch(phone_number: str, batch: TelemetryBatch):
        try:
            with open(TELEMETRY_FILE, "a", encoding="utf-8") as file:
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
            print(f"Telemetry Write Error: {e}")
