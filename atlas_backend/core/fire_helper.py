# atlas_backend/core/fire_helper.py
"""
Helper para computar diagnóstico FIRE por regime a partir do book_backtest.parquet.
Usado pelo endpoint GET /ativos/{ticker}/fire-diagnostico.
"""
import json
import math
import os
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from atlas_backend.core.paths import get_paths


def _safe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except Exception:
        return None


def _load_book_parquet() -> pd.DataFrame:
    """Carrega book_backtest.parquet. Retorna DataFrame vazio se não existir."""
    try:
        paths = get_paths()
        book_path = os.path.join(paths["book_dir"], "book_backtest.parquet")
        if not os.path.exists(book_path):
            return pd.DataFrame()
        return pd.read_parquet(book_path)
    except Exception:
        return pd.DataFrame()


def _load_ativo_json(ticker: str) -> Dict[str, Any]:
    """Carrega o master JSON do ativo."""
    paths = get_paths()
    config_path = os.path.join(paths["config_dir"], f"{ticker}.json")
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _compute_ir(pnl_values: List[float]) -> float:
    """Computa IR (Information Ratio) anualizado para uma lista de P&Ls."""
    if not pnl_values or len(pnl_values) < 2:
        return 0.0
    arr = np.array(pnl_values)
    media = np.mean(arr)
    desvio = np.std(arr, ddof=1)
    if desvio == 0:
        return 1.0 if media > 0 else 0.0
    return (media / desvio) * math.sqrt(252 / 21)


def compute_fire_diagnostico(ticker: str) -> Dict[str, Any]:
    """
    Computa diagnóstico FIRE completo por regime para o ticker informado.
    Lê de book_backtest.parquet (fonte primária) com fallback para master JSON.
    """
    ticker = ticker.strip().upper()

    # ── Carrega dados ──────────────────────────────────────────────
    df_book = _load_book_parquet()
    raw = _load_ativo_json(ticker)
    historico = raw.get("historico", []) or []
    total_ciclos = len(historico)

    # ── Filtra trades do ticker ────────────────────────────────────
    if df_book.empty:
        rows = []
    else:
        # Normaliza colunas
        df_ticker = df_book[df_book.get("ativo") == ticker].copy()
        if df_ticker.empty:
            # Tenta via 'core'
            if "core" in df_book.columns:
                df_ticker = df_book[df_book["core"].apply(
                    lambda x: isinstance(x, dict) and x.get("ativo") == ticker
                )].copy()

        rows = []
        for _, row in df_ticker.iterrows():
            core = row.get("core", {}) if isinstance(row.get("core"), dict) else {}
            orbit = row.get("orbit", {}) if isinstance(row.get("orbit"), dict) else {}

            # Ignora trades sem saída (ainda abertos)
            motivo_saida = core.get("motivo_saida")
            if motivo_saida is None:
                continue
            if core.get("motivo_nao_entrada"):
                continue

            rows.append({
                "regime": orbit.get("regime_entrada") or orbit.get("regime") or "DESCONHECIDO",
                "estrategia": core.get("estrategia"),
                "pnl": _safe_float(core.get("pnl")),
                "ciclo_id": orbit.get("ciclo_id") or core.get("ciclo_id"),
                "motivo_saida": str(motivo_saida).upper(),
                "data_entrada": row.get("data_entrada"),
                "data_saida": row.get("data_saida"),
            })

    # ── Fallback para historico ────────────────────────────────────
    if not rows and historico:
        for item in historico:
            regime = item.get("regime") or item.get("regime_entrada") or "DESCONHECIDO"
            estrategia = item.get("estrategia") or item.get("strategy")
            pnl = _safe_float(item.get("pnl"))
            rows.append({
                "regime": regime,
                "estrategia": estrategia,
                "pnl": pnl,
                "ciclo_id": item.get("ciclo_id"),
                "motivo_saida": str(item.get("motivo_saida", "")).upper(),
                "data_entrada": item.get("data_entrada"),
                "data_saida": item.get("data_saida"),
            })

    # ── Agrega por regime ──────────────────────────────────────────
    regimes_map: Dict[str, Dict[str, Any]] = {}
    stops_por_regime: Dict[str, int] = {}
    ciclos_operados: set = set()

    for row in rows:
        regime = row.get("regime") or "DESCONHECIDO"
        estrategia = row.get("estrategia")
        pnl = row.get("pnl")
        motivo_saida = row.get("motivo_saida", "")
        ciclo_id = row.get("ciclo_id")

        reg = regimes_map.setdefault(regime, {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "pnl_values": [],
            "wins_values": [],
            "losses_values": [],
            "worst_trade": None,
            "best_trade": None,
            "estrategias": {},
            "motivos_saida": {},
        })

        reg["trades"] += 1

        if isinstance(pnl, (int, float)):
            reg["pnl_values"].append(float(pnl))
            if pnl > 0:
                reg["wins"] += 1
                reg["wins_values"].append(float(pnl))
            else:
                reg["losses"] += 1
                reg["losses_values"].append(float(pnl))

            if reg["worst_trade"] is None or float(pnl) < reg["worst_trade"]:
                reg["worst_trade"] = float(pnl)
            if reg["best_trade"] is None or float(pnl) > reg["best_trade"]:
                reg["best_trade"] = float(pnl)

        if estrategia:
            reg["estrategias"][estrategia] = reg["estrategias"].get(estrategia, 0) + 1

        if ciclo_id:
            ciclos_operados.add(str(ciclo_id))
        elif estrategia:
            ciclos_operados.add(f"row_{len(ciclos_operados)}")

        if "STOP" in motivo_saida:
            stops_por_regime[regime] = stops_por_regime.get(regime, 0) + 1

        # Conta motivos de saída
        if motivo_saida:
            reg["motivos_saida"][motivo_saida] = reg["motivos_saida"].get(motivo_saida, 0) + 1

    ciclos_com_op = len(ciclos_operados)
    if ciclos_com_op == 0:
        ciclos_com_op = sum(1 for h in historico if h.get("estrategia"))

    # ── Monta saída por regime ─────────────────────────────────────
    regimes = []
    for regime, acc in regimes_map.items():
        trades = acc["trades"]
        wins = acc["wins"]
        losses = acc["losses"]
        acerto = (wins / trades * 100.0) if trades else 0.0

        pnl_values = acc["pnl_values"]
        wins_values = acc["wins_values"]
        losses_values = acc["losses_values"]

        ir_medio = _compute_ir(pnl_values)

        # Métricas adicionais
        avg_win = float(np.mean(wins_values)) if wins_values else 0.0
        avg_loss = float(np.mean(losses_values)) if losses_values else 0.0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0
        expectancy = (wins / trades * avg_win + losses / trades * avg_loss) if trades else 0.0

        # Estratégia dominante
        estrategia_dominante = None
        if acc["estrategias"]:
            estrategia_dominante = max(acc["estrategias"], key=acc["estrategias"].get)

        # Estratégias por contagem
        estrategias_counts = [
            {"estrategia": k, "trades": v}
            for k, v in sorted(acc["estrategias"].items(), key=lambda x: -x[1])
        ]

        regimes.append({
            "regime": regime,
            "trades": trades,
            "wins": wins,
            "losses": losses,
            "acerto_pct": round(acerto, 1),
            "ir": round(ir_medio, 3),
            "worst_trade": acc["worst_trade"],
            "best_trade": acc["best_trade"],
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "expectancy": round(expectancy, 2),
            "estrategia_dominante": estrategia_dominante,
            "estrategias": estrategias_counts,
            "motivos_saida": acc["motivos_saida"],
        })

    # ── Cobertura consolidada ──────────────────────────────────────
    total_trades = sum(r["trades"] for r in regimes)
    total_wins = sum(r["wins"] for r in regimes)
    acerto_geral = (total_wins / total_trades * 100.0) if total_trades else 0.0

    pnl_total = sum(r["trades"] > 0 and sum(
        [v for v in regimes_map[r["regime"]]["pnl_values"]]
    ) for r in regimes)
    pnl_total = sum(sum(regimes_map[r["regime"]]["pnl_values"]) for r in regimes if regimes_map[r["regime"]]["pnl_values"])

    cobertura = {
        "ciclos_com_operacao": ciclos_com_op,
        "total_ciclos": total_ciclos,
        "total_trades": total_trades,
        "acerto_geral_pct": round(acerto_geral, 1),
        "pnl_total": round(pnl_total, 2),
    }

    return {
        "ticker": ticker,
        "regimes": sorted(regimes, key=lambda r: r["regime"]),
        "cobertura": cobertura,
        "stops_por_regime": stops_por_regime,
        "fonte_dados": "book_backtest.parquet+master_json",
    }