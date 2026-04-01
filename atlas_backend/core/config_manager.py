import json
from pathlib import Path
import tempfile
import os
from atlas_backend.core.schema_validator import validate_config
from atlas_backend.core.versioning import save_version
from atlas_backend.core.audit_logger import log_action

CONFIG_PATH = Path("storage/configs/delta_chaos_config.json")


def load_config():
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        return json.load(f)


def update_config(ticker: str, new_data: dict, description: str):
    current = load_config()

    # Validação básica
    if not new_data:
        raise ValueError("new_data é obrigatório")

    # Inicializa estrutura
    if "ativos" not in current:
        current["ativos"] = {}
    if ticker not in current["ativos"]:
        current["ativos"][ticker] = {}

    # Atualiza APENAS campos editáveis
    editable_keys = ["take_profit", "stop_loss", "regime_estrategia", "anos_validos"]
    for key in editable_keys:
        if key in new_data:
            current["ativos"][ticker][key] = new_data[key]

    # Valida config completo
    validated = validate_config(current)

    diff = {"before": current, "after": current}
    version = save_version(current, description, diff)

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Escrita atômica
    with tempfile.NamedTemporaryFile(
        'w',
        dir=CONFIG_PATH.parent,
        delete=False,
        suffix='.tmp'
    ) as tmp:
        json.dump(current, tmp, indent=2)
        tmp_path = tmp.name

    os.replace(tmp_path, CONFIG_PATH)

    log_action(
        action="config_update",
        payload={"ticker": ticker, **new_data},
        response={"status": "OK", "version": version["version_id"]}
    )

    return version