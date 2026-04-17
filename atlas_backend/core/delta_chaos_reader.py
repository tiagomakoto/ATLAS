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
    return [
        Path(f).stem for f in files
        if "_corrupto_" not in Path(f).stem.lower()
    ]


def get_ativo_raw(ticker: str) -> Dict[str, Any]:
    """Carrega o JSON bruto de um ativo."""
    paths = get_paths()
    config_path = os.path.join(paths["config_dir"], f"{ticker}.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Ativo '{ticker}' não encontrado")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_date_flex(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except Exception:
            return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    text = str(value).strip()
    if not text:
        return None

    candidates = [text]
    if "T" not in text and len(text) == 7 and text.count("-") == 1:
        candidates.append(f"{text}-01")

    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except Exception:
            pass

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
            return parsed
        except Exception:
            pass
    return None


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _safe_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _read_book_backtest_ops() -> List[Dict[str, Any]]:
    paths = get_paths()
    book_dir = paths.get("book_dir")
    if not book_dir:
        return []
    book_path = os.path.join(book_dir, "book_backtest.json")
    if not os.path.exists(book_path):
        return []
    try:
        with open(book_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        ops = payload.get("ops", [])
        return ops if isinstance(ops, list) else []
    except Exception:
        return []


def get_cotahist_recente_info(ticker: str) -> Dict[str, Any]:
    """
    Retorna data de referência de atualização de dados para o guard do step 1.
    Fontes: master JSON + histórico do ativo + mtime de arquivos COTAHIST locais.
    """
    raw = get_ativo_raw(ticker)
    historico = raw.get("historico", [])
    calibracao = raw.get("calibracao", {})

    date_candidates = [
        raw.get("cotahist_ultimo_processado_em"),
        raw.get("ultimo_cotahist_processado_em"),
        raw.get("cotahist_atualizado_em"),
        raw.get("last_updated"),
        raw.get("atualizado_em"),
        calibracao.get("cotahist_ultimo_processado_em"),
    ]

    for item in historico[-48:]:
        date_candidates.extend(
            [
                item.get("data"),
                item.get("timestamp"),
                item.get("data_fim"),
                item.get("fim"),
                item.get("mes_ano"),
                item.get("ciclo_id"),
            ]
        )

    paths = get_paths()
    dc_base = paths.get("delta_chaos_base")
    if dc_base:
        cotahist_dir = os.path.join(dc_base, "TAPE", "cotahist")
        if os.path.isdir(cotahist_dir):
            try:
                latest_mtime = None
                for name in os.listdir(cotahist_dir):
                    if not str(name).upper().startswith("COTAHIST"):
                        continue
                    full = os.path.join(cotahist_dir, name)
                    if not os.path.isfile(full):
                        continue
                    mtime = os.path.getmtime(full)
                    if latest_mtime is None or mtime > latest_mtime:
                        latest_mtime = mtime
                if latest_mtime is not None:
                    date_candidates.append(
                        datetime.fromtimestamp(latest_mtime, tz=timezone.utc).isoformat()
                    )
            except Exception:
                pass

    parsed = [_parse_date_flex(v) for v in date_candidates]
    parsed = [d for d in parsed if d is not None]
    latest = max(parsed) if parsed else None

    if latest is None:
        return {
            "ticker": ticker,
            "data_ultimo_cotahist": None,
            "dias_desde_atualizacao": None,
            "dados_recentes": False,
            "fonte_data": "indisponivel",
        }

    now = datetime.now(timezone.utc)
    dias = max((now - latest).days, 0)
    return {
        "ticker": ticker,
        "data_ultimo_cotahist": latest.date().isoformat(),
        "dias_desde_atualizacao": dias,
        "dados_recentes": dias < 7,
        "fonte_data": "master_json+historico",
    }


_GATE_CRITERIOS_PADRAO = [
    "E1 Taxa de acerto",
    "E2 IR mínimo",
    "E3 N mínimo de trades",
    "E4 Consistência anual",
    "E5 IR por regime",
    "E6 Drawdown máximo",
    "E7 Consecutivos negativos",
    "E8 Cobertura de regimes",
]


def get_gate_resultado(ticker: str) -> Dict[str, Any]:
    """
    Retorna resultado GATE granular com leitura do master JSON e fallback robusto.
    """
    raw = get_ativo_raw(ticker)
    calibracao = raw.get("calibracao", {})
    gate_stored = calibracao.get("gate_resultado")
    if isinstance(gate_stored, dict) and gate_stored.get("criterios"):
        return gate_stored

    historico_config = raw.get("historico_config", [])
    gate_entry = None
    for item in reversed(historico_config):
        modulo = str(item.get("modulo", "")).upper()
        if "GATE" in modulo:
            gate_entry = item
            break

    historico = raw.get("historico", []) or []
    ultimo = historico[-1] if historico else {}
    ir_ultimo = _safe_float(ultimo.get("ir"))
    trades_ultimo = _safe_int(ultimo.get("trades")) or _safe_int(ultimo.get("n_trades"))

    gates_aprovados = None
    resultado = "BLOQUEADO"
    if gate_entry:
        gates_aprovados = gate_entry.get("gates_aprovados")
        resultado_raw = str(
            gate_entry.get("resultado")
            or gate_entry.get("gate_decisao")
            or gate_entry.get("valor_novo")
            or ""
        ).upper()
        if resultado_raw == "OPERAR":
            resultado = "OPERAR"
        elif resultado_raw in {"MONITORAR", "EXCLUIDO", "FALHA"}:
            resultado = "BLOQUEADO"

    criterios = []
    criterios_raw = None
    if gate_entry:
        if isinstance(gate_entry.get("criterios"), list):
            criterios_raw = gate_entry.get("criterios")
        elif isinstance(gate_entry.get("gates"), dict):
            criterios_raw = []
            for key, value in gate_entry.get("gates", {}).items():
                criterios_raw.append(
                    {
                        "id": str(key).split(" ")[0],
                        "nome": str(key),
                        "passou": bool(value),
                        "valor": "N/D",
                    }
                )

    if isinstance(criterios_raw, list) and criterios_raw:
        for idx, c in enumerate(criterios_raw, start=1):
            cid = str(c.get("id") or f"E{idx}")
            nome = c.get("nome") or c.get("criterio") or f"Critério {idx}"
            passou = bool(c.get("passou", False))
            valor = c.get("valor", "N/D")
            criterios.append({"id": cid, "nome": nome, "passou": passou, "valor": valor})

    if not criterios:
        default_values = {
            1: f"{ir_ultimo:.3f}" if ir_ultimo is not None else "N/D",
            2: f"{ir_ultimo:.3f}" if ir_ultimo is not None else "N/D",
            3: str(trades_ultimo) if trades_ultimo is not None else "N/D",
            4: "N/D",
            5: "N/D",
            6: "N/D",
            7: "N/D",
            8: "N/D",
        }
        gates_pass_count = gates_aprovados if isinstance(gates_aprovados, int) else 0
        for idx, nome in enumerate(_GATE_CRITERIOS_PADRAO, start=1):
            passou = idx <= max(min(gates_pass_count, 8), 0)
            criterios.append(
                {
                    "id": f"E{idx}",
                    "nome": nome,
                    "passou": bool(passou),
                    "valor": default_values[idx],
                }
            )

    falhas = [c["id"] for c in criterios if not c["passou"]]
    ciclo = None
    if historico:
        ciclo = historico[-1].get("ciclo_id") or historico[-1].get("mes_ano")

    return {
        "ticker": ticker,
        "ciclo": ciclo,
        "criterios": criterios,
        "resultado": resultado,
        "falhas": falhas if resultado != "OPERAR" else [],
        "fonte_dados": "master_json",
    }


def get_fire_diagnostico(ticker: str) -> Dict[str, Any]:
    """
    Retorna diagnóstico FIRE por regime.
    Fonte primária: book_backtest.json (trades fechados).
    Fallback: historico do master JSON.
    """
    raw = get_ativo_raw(ticker)
    calibracao = raw.get("calibracao", {})
    fire_stored = calibracao.get("fire_diagnostico")
    if isinstance(fire_stored, dict) and fire_stored.get("regimes"):
        return fire_stored

    historico = raw.get("historico", []) or []
    total_ciclos = len(historico)
    regimes_map: Dict[str, Dict[str, Any]] = {}
    stops_por_regime: Dict[str, int] = {}

    rows = []
    for op in _read_book_backtest_ops():
        core = op.get("core", {}) if isinstance(op, dict) else {}
        orbit = op.get("orbit", {}) if isinstance(op, dict) else {}
        if core.get("ativo") != ticker:
            continue
        if core.get("motivo_saida") is None:
            continue
        if core.get("motivo_nao_entrada"):
            continue
        rows.append(
            {
                "regime": orbit.get("regime_entrada") or orbit.get("regime") or "DESCONHECIDO",
                "estrategia": core.get("estrategia"),
                "pnl": _safe_float(core.get("pnl")),
                "ciclo_id": orbit.get("ciclo_id") or core.get("ciclo_id"),
                "motivo_saida": str(core.get("motivo_saida", "")).upper(),
            }
        )

    if not rows:
        for item in historico:
            rows.append(
                {
                    "regime": (
                        item.get("regime")
                        or item.get("regime_entrada")
                        or item.get("regime_atual")
                        or "DESCONHECIDO"
                    ),
                    "estrategia": item.get("estrategia") or item.get("strategy"),
                    "pnl": _safe_float(item.get("pnl")),
                    "ciclo_id": item.get("ciclo_id"),
                    "motivo_saida": str(item.get("motivo_saida", "")).upper(),
                }
            )

    ciclos_operados = set()
    for row in rows:
        regime = row.get("regime") or "DESCONHECIDO"
        estrategia = row.get("estrategia")
        pnl = row.get("pnl")
        motivo_saida = row.get("motivo_saida", "")

        reg = regimes_map.setdefault(
            regime,
            {
                "trades": 0,
                "wins": 0,
                "pnl_values": [],
                "worst_trade": None,
                "estrategias": {},
            },
        )
        reg["trades"] += 1

        if isinstance(pnl, (int, float)):
            reg["pnl_values"].append(float(pnl))
            if pnl > 0:
                reg["wins"] += 1
            if reg["worst_trade"] is None or float(pnl) < reg["worst_trade"]:
                reg["worst_trade"] = float(pnl)

        if estrategia:
            reg["estrategias"][estrategia] = reg["estrategias"].get(estrategia, 0) + 1

        ciclo_id = row.get("ciclo_id")
        if ciclo_id:
            ciclos_operados.add(str(ciclo_id))
        elif estrategia:
            ciclos_operados.add(f"row_{len(ciclos_operados)}")

        if "STOP" in motivo_saida:
            stops_por_regime[regime] = stops_por_regime.get(regime, 0) + 1

    ciclos_com_op = len(ciclos_operados)
    if ciclos_com_op == 0:
        ciclos_com_op = sum(1 for h in historico if h.get("estrategia"))

    regimes = []
    for regime, acc in regimes_map.items():
        trades = acc["trades"]
        acerto = (acc["wins"] / trades * 100.0) if trades else 0.0

        ir_medio = 0.0
        if len(acc["pnl_values"]) > 1:
            media = sum(acc["pnl_values"]) / len(acc["pnl_values"])
            variancia = sum((x - media) ** 2 for x in acc["pnl_values"]) / (len(acc["pnl_values"]) - 1)
            desvio = variancia ** 0.5
            if desvio > 0:
                ir_medio = (media / desvio) * ((252.0 / 21.0) ** 0.5)
        elif len(acc["pnl_values"]) == 1 and acc["pnl_values"][0] > 0:
            ir_medio = 1.0

        estrategia_dominante = None
        if acc["estrategias"]:
            estrategia_dominante = max(acc["estrategias"], key=acc["estrategias"].get)

        regimes.append(
            {
                "regime": regime,
                "trades": trades,
                "acerto_pct": round(acerto, 1),
                "ir": round(ir_medio, 3),
                "worst_trade": acc["worst_trade"],
                "estrategia_dominante": estrategia_dominante,
            }
        )

    return {
        "ticker": ticker,
        "regimes": sorted(regimes, key=lambda r: r["regime"]),
        "cobertura": {
            "ciclos_com_operacao": ciclos_com_op,
            "total_ciclos": total_ciclos,
        },
        "stops_por_regime": stops_por_regime,
        "fonte_dados": "book_backtest+master_json",
    }


def get_ativo(ticker: str) -> Dict[str, Any]:
    """Carrega a configuração de um ativo específico COM DADOS ENRIQUECIDOS."""
    paths = get_paths()
    config_path = os.path.join(paths["config_dir"], f"{ticker}.json")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Ativo '{ticker}' não encontrado")

    raw_data = get_ativo_raw(ticker)

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
                "3_gate_fire": {"status": "idle", "iniciado_em": None, "concluido_em": None, "erro": None}
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
