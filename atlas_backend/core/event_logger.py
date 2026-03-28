from datetime import datetime
from core.event_bus import emit_event

def log_event(event: str, details: dict):
    payload = {
        "type": "event",
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "details": details
    }

    emit_event(payload)