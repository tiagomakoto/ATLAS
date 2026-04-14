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

    # ✅ A05: Extrair e sanitizar reflect_historico (de reflect_cycle_history)
    # Filtrar apenas ciclos que existem no historico ORBIT atual
    ciclos_orbit = {c["ciclo_id"] for c in historico if "ciclo_id" in c}
    reflect_cycle_history = raw_data.get("reflect_cycle_history", {})
    reflect_historico = []
    for ciclo_id, dados in sorted(reflect_cycle_history.items()):
        if ciclo_id not in ciclos_orbit:
            continue  # ciclo órfão — não existe no historico atual
        record = {
            "ciclo_id": ciclo_id,
            "reflect_state": dados.get("reflect_state"),
            "reflect_score": dados.get("score_reflect"),
            "aceleracao": dados.get("aceleracao"),
            "delta_ir": dados.get("delta_ir"),
            "iv_prem_ratio": dados.get("iv_media"),
            "ret_vol_ratio": dados.get("rv_media"),
            "fonte_divergencia": dados.get("fonte_divergencia"),
            "divergencia_disponivel": dados.get("divergencia_disponivel"),
        }
        reflect_historico.append(sanitize_record(record))

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

    core["estrategias"] = raw_data.get("estrategias", {})

    # ✅ Determinar status (SEM_EDGE / OPERAR / MONITORAR / SUSPENSO)
    ultimo_ciclo = historico[-1] if historico else {}

    if not historico or ultimo_ciclo.get("lock"):
        status = "SUSPENSO"
    else:
        historico_config = raw_data.get("historico_config", [])
        reflect_state = raw_data.get("reflect_state", "B")
        reflect_history = raw_data.get("reflect_history", [])

        # Quedas consecutivas REFLECT (D ou E)
        quedas_consecutivas = 0
        for r in reversed(reflect_history[-5:]):
            if r.get("state", "?") in ("D", "E"):
                quedas_consecutivas += 1
            else:
                break

        # Último GATE completo
        ultimo_gate = None
        for cfg in reversed(historico_config):
            if "GATE" in cfg.get("modulo", ""):
                resultado = (
                    cfg.get("resultado")
                    or cfg.get("gate_decisao")
                    or cfg.get("valor_novo")
                )
                if resultado in ("OPERAR", "MONITORAR"):
                    ultimo_gate = resultado
                    break

        ir_atual = ultimo_ciclo.get("ir", 0) or 0

        if quedas_consecutivas >= 2:
            status = "SUSPENSO"
        elif ultimo_gate == "OPERAR" and ir_atual > 0 and reflect_state in ("A", "B"):
            status = "OPERAR"
        elif ultimo_gate in ("OPERAR", "MONITORAR"):
            status = "MONITORAR"
        else:
            status = "SEM_EDGE"

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

    # ✅ Retornar estrutura completa COM TP E STOP LOSS E ONBOARDING
    return {
        "ticker": ticker,
        "status": status,
        "core": core,
        "historico": historico,
        "historico_config": len(raw_data.get("historico_config", [])) > 0, # ← BOOLEANO: true se tem registros
        "reflect_historico": reflect_historico,
        "reflect_state": raw_data.get("reflect_state", "B"),
        "staleness_days": staleness_days,
        "ultimo_ciclo": ultimo_ciclo,
        "version": raw_data.get("version", 0),
        "last_updated": last_updated,
        # ✅ CAMPOS OBRIGATÓRIOS PARA MANUTENÇÃO:
        "take_profit": raw_data.get("take_profit"),
        "stop_loss": raw_data.get("stop_loss"),
        # ✅ NOVO: campo calibracao com estrutura padrão
        "calibracao": raw_data.get("calibracao", {
            "step_atual": 1,
            "steps": {
                "1_backtest_dados": {"status": "idle", "iniciado_em": None, "concluido_em": None, "erro": None},
                "2_tune": {"status": "idle", "iniciado_em": None, "concluido_em": None, "erro": None, "trials_completos": 0, "trials_total": 200},
                "3_backtest_gate": {"status": "idle", "iniciado_em": None, "concluido_em": None, "erro": None}
            },
            "ultimo_evento_em": None
        })
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