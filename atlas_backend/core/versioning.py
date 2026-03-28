import json
import uuid
from pathlib import Path
from datetime import datetime

VERSIONS_DIR = Path("storage/versions")


def save_version(data: dict, description: str, diff: dict) -> dict:
    """
    Salva uma versão imutável do config com metadados.
    Retorna dict com version_id e timestamp.
    """
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

    version_id = str(uuid.uuid4())[:8]
    timestamp = datetime.utcnow().isoformat()

    record = {
        "version_id": version_id,
        "timestamp": timestamp,
        "description": description,
        "diff": diff,
        "snapshot": data,
    }

    path = VERSIONS_DIR / f"{timestamp.replace(':', '-')}_{version_id}.json"

    with open(path, "w") as f:
        json.dump(record, f, indent=2)

    return record


def list_versions(n: int = 20) -> list:
    """
    Retorna as últimas n versões salvas, ordem cronológica decrescente.
    """
    if not VERSIONS_DIR.exists():
        return []

    files = sorted(VERSIONS_DIR.glob("*.json"), reverse=True)

    versions = []
    for f in files[:n]:
        try:
            with open(f) as fp:
                v = json.load(fp)
                versions.append({
                    "version_id": v.get("version_id"),
                    "timestamp": v.get("timestamp"),
                    "description": v.get("description"),
                })
        except Exception:
            continue

    return versions
