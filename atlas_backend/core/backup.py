import shutil
from datetime import datetime
from pathlib import Path
from core.audit_logger import log_action

SOURCE_DIRS = [
    Path("storage/configs"),
    Path("storage/logs"),
    Path("storage/versions")
]

BACKUP_DIR = Path("backups")

def run_backup():
    timestamp = datetime.utcnow().isoformat().replace(":", "-")
    target = BACKUP_DIR / timestamp

    try:
        target.mkdir(parents=True, exist_ok=True)

        for src in SOURCE_DIRS:
            if src.exists():
                shutil.copytree(src, target / src.name)

        log_action(
            action="backup_success",
            payload={},
            response={"status": "OK", "backup_path": str(target)}
        )

    except Exception as e:
        # 🔴 ALERTA VISÍVEL
        log_action(
            action="backup_failure",
            payload={},
            response={
                "status": "ERROR",
                "error": str(e)
            }
        )

        raise RuntimeError(f"BACKUP FAILED: {str(e)}")