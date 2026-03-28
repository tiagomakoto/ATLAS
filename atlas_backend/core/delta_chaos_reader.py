# atlas_backend/core/delta_chaos_reader.py
import json
import os
import glob
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any
from core.paths import get_paths

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
        data = json.load(f)
    
    # ✅ Extrair historico como ARRAY
    historico = data.get("historico", [])
    if not isinstance(historico, list):
        historico = []
    
    # ✅ Extrair core
    core = data.get("core", {})
    if not core:
        core = {
            "estrategia": data.get("estrategia"),
            "ativo": data.get("ativo", ticker),
            "tune_horizon": data.get("tune_horizon"),
            "vol_target": data.get("vol_target")
        }
    
    # ✅ Extrair estrategia: core.estrategia OU data.estrategia OU ultimo_ciclo.estrategia
    estrategia = (
        core.get("estrategia") or 
        data.get("estrategia") or 
        (historico[-1].get("estrategia") if historico else None)
    )
    
    # ✅ NÃO usar fallback "Short Vol" — deixar None se não existir
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
    
    # ✅ Calcular staleness_days a partir de last_updated OU file mtime
    last_updated = data.get("last_updated")
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
        # Fallback: calcular a partir da data de modificação do arquivo
        try:
            file_mtime = os.path.getmtime(config_path)
            last_dt = datetime.fromtimestamp(file_mtime, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            staleness_days = (now - last_dt).days
        except Exception:
            staleness_days = 0
    
    # ✅ Retornar estrutura completa
    return {
        "ticker": ticker,
        "status": status,
        "core": core,
        "historico": historico,
        "staleness_days": staleness_days,
        "ultimo_ciclo": ultimo_ciclo,
        "version": data.get("version", 0),
        "last_updated": last_updated
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