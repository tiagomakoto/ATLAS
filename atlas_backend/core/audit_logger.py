import json
from pathlib import Path
from datetime import datetime

LOG_PATH = Path("storage/logs/audit.log")


def log_action(action: str, payload: dict, response: dict):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user": "CEO",
        "action": action,
        "payload": payload,
        "response": response,
    }

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def load_audit_log(n: int = 50):
    """
    Lê as últimas n entradas do log de auditoria.
    Retorna lista de dicts — entradas malformadas são ignoradas.
    """
    if not LOG_PATH.exists():
        return []

    entries = []

    with open(LOG_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return entries[-n:]