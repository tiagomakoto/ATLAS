import json
import os
from pathlib import Path

def get_paths() -> dict:
    config_path = Path(__file__).parent.parent / "config" / "paths.json"
    
    if not config_path.exists():
        return {
            "config_dir": os.path.expanduser("~/DeltaChaos/configs"),
            "ohlcv_dir": os.path.expanduser("~/DeltaChaos/data"),
            "history_dir": os.path.expanduser("~/DeltaChaos/history"),
            "book_dir": os.path.expanduser("~/DeltaChaos/book"),
        }
    
    with open(config_path, 'r', encoding='utf-8') as f:
        paths = json.load(f)
    
    # ✅ Remove espaços das chaves E valores
    return {k.strip(): v.strip().replace("/", "\\") if isinstance(v, str) else v for k, v in paths.items()}