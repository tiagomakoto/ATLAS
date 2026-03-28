import json
from pathlib import Path
from datetime import datetime
from models.audit_schema import AuditLogEntry

LOG_PATH = Path("storage/logs/audit.log")

def log_action(action: str, payload: dict, response: dict):
    entry = AuditLogEntry(
        timestamp=datetime.utcnow(),
        action=action,
        payload=payload,
        response=response
    )

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(LOG_PATH, "a") as f:
        f.write(entry.json() + "\n")