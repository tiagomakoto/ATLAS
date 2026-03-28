from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict

class AuditLogEntry(BaseModel):
    timestamp: datetime
    user: str = "CEO"  # 🔒 hardcoded conforme SCAN
    action: str
    payload: Dict[str, Any]
    response: Dict[str, Any]