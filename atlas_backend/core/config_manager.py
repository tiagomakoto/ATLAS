import json
from pathlib import Path
import tempfile
import os

from core.schema_validator import validate_config
from core.versioning import save_version
from core.audit_logger import log_action

CONFIG_PATH = Path("storage/configs/delta_chaos_config.json")

def load_config():
    if not CONFIG_PATH.exists():
        return {}

    with open(CONFIG_PATH) as f:
        return json.load(f)

def update_config(new_data: dict, description: str):
    current = load_config()

    validated = validate_config(new_data)

    diff = {
        "before": current,
        "after": new_data
    }

    version = save_version(new_data, description, diff)

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # ✅ ESCRITA ATÔMICA (correção crítica)
    with tempfile.NamedTemporaryFile(
        'w',
        dir=CONFIG_PATH.parent,
        delete=False,
        suffix='.tmp'
    ) as tmp:
        json.dump(new_data, tmp, indent=2)
        tmp_path = tmp.name

    os.replace(tmp_path, CONFIG_PATH)

    log_action(
        action="config_update",
        payload=new_data,
        response={"status": "OK", "version": version["version_id"]}
    )

    return version