# atlas_backend/core/delta_chaos_reader.py
import json
import os
import glob
import math
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any
from atlas_backend.core.paths import get_paths


def sanitize_nan(value):
    """Converte NaN Python para None (JSON válido)."""
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def sanitize_record(record: dict) -> dict:
    """Aplica sanitize_nan a todos os valores de um record."""
    return {k: sanitize_nan(v) for k, v in record.items()}


def list_ativos() -> List[str]:
    """Lista todos os ativos disponíveis no diretório de configs."""
    paths = get_paths()
    pattern = os.path.join(paths["config_dir"], "*.json")
    files = glob.glob(pattern)
    return [Path(f).stem for f in files]


def get_ativo(ticker: str) -> Dict[str, Any]:
    """Carrega a configuração de um ativo específico COM DADOS ENRIQUECIDOS."""
    paths = get_paths()
    config_path = os.path.join(paths["config_dir"], f"{ticker}.json")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Ativo '{ticker}' não encontrado")

    with open(config_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    # ✅ Extrair historico como ARRAY
    historico = raw_data.get("historico", [])
    if not isinstance(historico, list):
        historico = []

    # ✅ A05: Extrair e sanitizar reflect_historico (de reflect_all_cycles_history)
    reflect_historico_raw = raw_data.get("reflect_all_cycles_history", [])
    reflect_historico = [sanitize_record(r) for r in reflect_historico_raw]
    
    # ✅ Extrair reflect_permanent_block
    reflect_permanent_block = raw_data.get("reflect_permanent_block_flag", False)

    # ✅ Extrair core
    core = raw_data.get("core", {})
    if not core:
        core = {
            "estrategia": raw_data.get("estrategia"),
            "ativo": raw_data.get("ativo", ticker),
            "tune_horizon": raw_data.get("tune_horizon"),
            "vol_target": raw_data.get("vol_target")
        }

    # ✅ Extrair estrategia
    estrategia = (
        core.get("estrategia") or 
        raw_data.get("estrategia") or 
        (historico[-1].get("estrategia") if historico else None)
    )

    if estrategia:
        core["estrategia"] = estrategia

    # ✅ Determinar status
    ultimo_ciclo = historico[-1] if historico else {}

    if not historico:
        status = "dormente"
    elif ultimo_ciclo.get("lock"):
        status = "impedido"
    else:
        status = "parametrizado"

    # ✅ Calcular staleness_days
    last_updated = raw_data.get("last_updated")
    if last_updated:
        try:
            if isinstance(last_updated, (int, float)):
                last_dt = datetime.fromtimestamp(last_updated, tz=timezone.utc)
            else:
                last_dt = datetime.fromisoformat(str(last_updated).replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            staleness_days = (now - last_dt).days
        except Exception:
            staleness_days = 0
    else:
        try:
            file_mtime = os.path.getmtime(config_path)
            last_dt = datetime.fromtimestamp(file_mtime, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            staleness_days = (now - last_dt).days
        except Exception:
            staleness_days = 0

    # ✅ Retornar estrutura completa COM TP E STOP LOSS
    return {
        "ticker": ticker,
        "status": status,
        "core": core,
        "historico": historico,
        "reflect_historico": reflect_historico,
        "reflect_permanent_block": reflect_permanent_block,
        "staleness_days": staleness_days,
        "ultimo_ciclo": ultimo_ciclo,
        "version": raw_data.get("version", 0),
        "last_updated": last_updated,
        # ✅ CAMPOS OBRIGATÓRIOS PARA MANUTENÇÃO:
        "take_profit": raw_data.get("take_profit"),
        "stop_loss": raw_data.get("stop_loss")
    }


def update_ativo(ticker: str, updates: Dict[str, Any], description: str) -> Dict[str, Any]:
    """Atualiza a configuração de um ativo com versionamento."""
    paths = get_paths()
    config_path = os.path.join(paths["config_dir"], f"{ticker}.json")
    history_path = os.path.join(paths["history_dir"], f"{ticker}_history.json")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Ativo '{ticker}' não encontrado")

    with open(config_path, 'r', encoding='utf-8') as f:
        current = json.load(f)

    if os.path.exists(history_path):
        with open(history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []

    history.append({
        "timestamp": current.get("last_updated"),
        "description": description,
        "snapshot": current
    })

    current.update(updates)
    current["last_updated"] = datetime.now(timezone.utc).isoformat()
    current["version"] = current.get("version", 0) + 1

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(current, f, indent=2, ensure_ascii=False)

    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    return {"status": "updated", "version": current["version"]}


def get_book(fonte: str) -> Dict[str, Any]:
    """Retorna posições abertas e trades do book."""
    if fonte not in ("backtest", "paper", "live"):
        raise ValueError(f"fonte inválida: {fonte}. Aceitos: backtest | paper | live")
    
    paths = get_paths()
    book_path = os.path.join(paths["book_dir"], f"book_{fonte}.json")

    if not os.path.exists(book_path):
        raise FileNotFoundError(f"BOOK_{fonte.upper()} não encontrado: {book_path}")

    with open(book_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return {
        "fonte": fonte,
        "posicoes_abertas": data.get("ops", []),
        "trades": [],
        "pnl_total": sum(
            op.get("core", {}).get("pnl", 0) or 0
            for op in data.get("ops", [])
            if op.get("core", {}).get("pnl")
        ),
        "delta_liquido": 0.0,
        "cobertura_put_itm": 0.0
    }