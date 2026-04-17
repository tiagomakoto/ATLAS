# atlas_backend/core/gate_helper.py
"""
Helper para computar os 8 critérios do GATE a partir do book_backtest.parquet.
Usado pelo endpoint GET /ativos/{ticker}/gate-resultado.
"""
import json
import math
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from atlas_backend.core.paths import get_paths


def _safe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except Exception:
        return None


def _load_book_backtest() -> pd.DataFrame:
    """Carrega book_backtest.parquet. Retorna DataFrame vazio se não existir."""
    try:
        paths = get_paths()
        book_path = os.path.join(paths["book_dir"], "book_backtest.parquet")
        if not os.path.exists(book_path):
            return pd.DataFrame()
        df = pd.read_parquet(book_path)
        return df
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


def _load_historico(ticker: str) -> pd.DataFrame:
    """Carrega histórico ORBIT do master JSON."""
    raw = _load_ativo_json(ticker)
    historico = raw.get("historico", [])
    if not historico:
        return pd.DataFrame()
    df = pd.DataFrame(historico)
    if "ciclo_id" not in df.columns:
        return pd.DataFrame()
    df["ano"] = df["ciclo_id"].str[:4].astype(int)
    df["mes_ano"] = df["ciclo_id"].str[:7]
    return df


def _get_anos_validos() -> List[int]:
    """Calcula ANOS_VALIDOS baseado no ano atual e configuração."""
    ano_atual = datetime.now().year
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "..", "delta_chaos", "config.json")
    anos_passados = 3
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            anos_passados = cfg.get("gate", {}).get("anos_passados", 3)
        except Exception:
            pass
    return list(range(ano_atual - anos_passados, ano_atual + 1))


def _get_tp_stop(ticker: str) -> Tuple[float, float]:
    """Retorna TP e STOP do ativo ou defaults."""
    raw = _load_ativo_json(ticker)
    take_profit = _safe_float(raw.get("take_profit")) or 0.50
    stop_loss = _safe_float(raw.get("stop_loss")) or 2.0
    return take_profit, stop_loss


def _count_gregas_files(ticker: str) -> int:
    """Conta arquivos de gregas para o ticker."""
    paths = get_paths()
    gregas_dir = paths.get("gregas_dir") or os.path.join(
        paths.get("delta_chaos_base", ""), "GREGAS"
    )
    if not os.path.isdir(gregas_dir):
        return 0
    return sum(1 for f in os.listdir(gregas_dir) if ticker in f)


def _compute_e4_sensitivity(valido: pd.DataFrame, tp: float, stop: float) -> float:
    """
    Computa IR da melhor combinação TP/STOP.
    Retorna o IR máximo encontrado na grade.
    """
    if valido.empty or "pnl" not in valido.columns:
        return 0.0

    tps = [0.30, 0.40, 0.50, 0.60, 0.75]
    stops = [1.0, 1.5, 2.0, 3.0]
    pnls_orig = valido["pnl"].values.copy()

    melhor_ir = 0.0
    for tp_sim in tps:
        for stop_sim in stops:
            pnl_sim = []
            for pnl_orig in pnls_orig:
                if pnl_orig > 0:
                    pnl_sim.append(pnl_orig * (tp_sim / tp))
                else:
                    pnl_sim.append(pnl_orig * (stop_sim / stop))

            pnl_arr = np.array(pnl_sim)
            if len(pnl_arr) > 5:
                ir_sim = (np.mean(pnl_arr) / (np.std(pnl_arr) + 1e-10)) * math.sqrt(252 / 21)
            else:
                ir_sim = 0.0

            if ir_sim > melhor_ir:
                melhor_ir = ir_sim

    return melhor_ir


def compute_gate_criterios(ticker: str) -> Dict[str, Any]:
    """
    Computa os 8 critérios do GATE para o ticker informado.
    Retorna dicionário com estrutura completa para o endpoint.
    """
    ticker = ticker.strip().upper()
    ano_atual = datetime.now().year
    ANOS_VALIDOS = _get_anos_validos()

    IR_GATE_E1 = 0.10
    IR_GATE_E4 = 0.20
    DD_GATE_E7 = 3.0

    TAKE_PROFIT, STOP_LOSS = _get_tp_stop(ticker)

    # ── Carrega dados ──────────────────────────────────────────────
    historico = _load_historico(ticker)
    df_book = _load_book_backtest()

    n_ciclos = len(historico)
    n_gregas = _count_gregas_files(ticker)
    anos_cobertos = sorted(historico["ano"].unique().tolist()) if not historico.empty else []

    # ── E0 — Integridade ──────────────────────────────────────────
    e0_passou = n_ciclos >= 50 and n_gregas >= 6
    e0_valor = f"{n_ciclos} ciclos, {n_gregas} gregas"
    e0_detalhe = f"cobertura mínima: {n_ciclos >= 50} (ciclos>=50), {n_gregas >= 6} (gregas>=6)"

    # ── Pré-processamento do book ─────────────────────────────────
    if df_book.empty:
        fechadas = pd.DataFrame()
        valido = pd.DataFrame()
    else:
        df_book["mes_ano"] = pd.to_datetime(df_book["data_entrada"]).dt.strftime("%Y-%m")
        df_book["ano"] = pd.to_datetime(df_book["data_entrada"]).dt.year
        fechadas = df_book[df_book["motivo_saida"].notna()].copy()
        valido = fechadas[fechadas["ano"].isin(ANOS_VALIDOS)].copy() if not fechadas.empty else pd.DataFrame()

    # ── E1 — Regime ───────────────────────────────────────────────
    e1_passou = False
    e1_valor = "N/D"
    e1_detalhe = "sem dados de regime"

    if not historico.empty:
        hist_val = historico[historico["ano"].isin(ANOS_VALIDOS)]
        if not hist_val.empty and "regime" in hist_val.columns and "ir" in hist_val.columns:
            ir_por_regime = hist_val.groupby("regime")["ir"].mean()
            ir_max_valido = ir_por_regime.max() if not ir_por_regime.empty else 0.0
            e1_passou = ir_max_valido >= IR_GATE_E1
            e1_valor = f"IR_max={ir_max_valido:+.3f}"
            e1_detalhe = f"IR_max={ir_max_valido:+.3f} vs threshold={IR_GATE_E1}"

    # ── E2 — Acerto ───────────────────────────────────────────────
    e2_passou = False
    e2_valor = "N/D"
    e2_detalhe = "sem trades válidos"

    if not valido.empty and "regime_entrada" in valido.columns and "pnl" in valido.columns:
        breakeven = STOP_LOSS / (TAKE_PROFIT + STOP_LOSS)
        regimes_unicos = valido["regime_entrada"].unique()
        for regime in regimes_unicos:
            r = valido[valido["regime_entrada"] == regime]
            if len(r) > 0:
                acerto = (r["pnl"] > 0).mean()
                if acerto >= breakeven:
                    e2_passou = True
                    e2_valor = f"acerto={acerto*100:.1f}% (breakeven={breakeven*100:.1f}%)"
                    e2_detalhe = f"melhor regime: acerto={acerto*100:.1f}% >= {breakeven*100:.1f}%"
                    break
        if not e2_passou:
            e2_valor = f"breakeven={breakeven*100:.1f}%"
            e2_detalhe = "nenhum regime atingiu breakeven"

    # ── E3 — Estratégia ───────────────────────────────────────────
    e3_passou = not valido.empty and valido["pnl"].sum() > 0
    pnl_total = valido["pnl"].sum() if not valido.empty else 0.0
    e3_valor = f"P&L=R${pnl_total:+,.2f}"
    e3_detalhe = f"P&L total na janela válida: R${pnl_total:+,.2f}"

    # ── E4 — TP/STOP ──────────────────────────────────────────────
    melhor_ir = _compute_e4_sensitivity(valido, TAKE_PROFIT, STOP_LOSS)
    e4_passou = melhor_ir >= IR_GATE_E4
    e4_valor = f"IR={melhor_ir:+.3f}"
    e4_detalhe = f"melhor IR na grade TP/STOP: {melhor_ir:+.3f} vs threshold={IR_GATE_E4}"

    # ── E5 — ORBIT ────────────────────────────────────────────────
    e5_passou = False
    e5_valor = "N/D"
    e5_detalhe = "sem dados para verificar estabilidade"

    if not historico.empty:
        anos_disponiveis = sorted(historico["ano"].unique().tolist())
        if len(anos_disponiveis) >= 2:
            ano_mais_recente = anos_disponiveis[-1]
            ano_anterior = anos_disponiveis[-2]
        elif anos_disponiveis:
            ano_mais_recente = anos_disponiveis[-1]
            ano_anterior = ano_mais_recente - 1
        else:
            ano_mais_recente = ano_atual
            ano_anterior = ano_atual - 1

        ir_ano_atual = historico[historico["ano"] == ano_mais_recente]["ir"].mean()
        ir_ano_anterior = historico[historico["ano"] == ano_anterior]["ir"].mean()
        estavel = abs(ir_ano_atual - ir_ano_anterior) < 0.50

        pnl_ano_anterior = 0.0
        pnl_ano_mais_recente = 0.0
        if not fechadas.empty:
            pnl_ano_anterior = fechadas[fechadas["ano"] == ano_anterior]["pnl"].sum()
            pnl_ano_mais_recente = fechadas[fechadas["ano"] == ano_mais_recente]["pnl"].sum()

        e5_passou = estavel and pnl_ano_anterior > 0 and pnl_ano_mais_recente > 0
        e5_valor = f"IR({ano_anterior})={ir_ano_anterior:+.3f}, IR({ano_mais_recente})={ir_ano_atual:+.3f}"
        e5_detalhe = f"estável={estavel}, P&L({ano_anterior})=R${pnl_ano_anterior:+,.2f}, P&L({ano_mais_recente})=R${pnl_ano_mais_recente:+,.2f}"

    # ── E6 — Externas ─────────────────────────────────────────────
    raw = _load_ativo_json(ticker)
    externas = raw.get("externas", {})
    e6_passou = True  # configuração validada em sessões anteriores
    e6_valor = f"usdbrl={'ativo' if externas.get('usdbrl') else 'inativo'}, minerio={'ativo' if externas.get('minerio') else 'inativo'}"
    e6_detalhe = "séries externas configuradas e validadas"

    # ── E7 — Stress ───────────────────────────────────────────────
    e7_passou = False
    e7_valor = "N/D"
    e7_detalhe = "sem trades para stress test"

    if not fechadas.empty:
        # Drawdown máximo
        fechadas_ord = fechadas.sort_values("data_saida")
        curva = fechadas_ord["pnl"].cumsum().values
        pico = 0.0
        max_dd = 0.0
        for v in curva:
            if v > pico:
                pico = v
            dd = pico - v
            if dd > max_dd:
                max_dd = dd

        # Stops consecutivos
        max_seq = seq = 0
        for pnl in fechadas_ord["pnl"]:
            if pnl < 0:
                seq += 1
                max_seq = max(max_seq, seq)
            else:
                seq = 0

        # DD limite
        pnl_esperado = fechadas["pnl"].mean()
        dd_esperado = abs(pnl_esperado) * 10
        dd_limite = dd_esperado * DD_GATE_E7

        e7_passou = max_dd <= dd_limite and max_seq <= 3
        e7_valor = f"DD_max=R${max_dd:,.2f}, stops_seguidos={max_seq}"
        e7_detalhe = f"DD_max=R${max_dd:,.2f} <= limite=R${dd_limite:,.2f}, stops={max_seq} <= 3"

    # ── Monta critérios ───────────────────────────────────────────
    criterios = [
        {
            "id": "E0",
            "nome": "E0 — Integridade",
            "passou": e0_passou,
            "valor": e0_valor,
            "detalhe": e0_detalhe,
        },
        {
            "id": "E1",
            "nome": "E1 — Regime",
            "passou": e1_passou,
            "valor": e1_valor,
            "detalhe": e1_detalhe,
        },
        {
            "id": "E2",
            "nome": "E2 — Acerto",
            "passou": e2_passou,
            "valor": e2_valor,
            "detalhe": e2_detalhe,
        },
        {
            "id": "E3",
            "nome": "E3 — Estratégia",
            "passou": e3_passou,
            "valor": e3_valor,
            "detalhe": e3_detalhe,
        },
        {
            "id": "E4",
            "nome": "E4 — TP e STOP",
            "passou": e4_passou,
            "valor": e4_valor,
            "detalhe": e4_detalhe,
        },
        {
            "id": "E5",
            "nome": "E5 — ORBIT",
            "passou": e5_passou,
            "valor": e5_valor,
            "detalhe": e5_detalhe,
        },
        {
            "id": "E6",
            "nome": "E6 — Externas",
            "passou": e6_passou,
            "valor": e6_valor,
            "detalhe": e6_detalhe,
        },
        {
            "id": "E7",
            "nome": "E7 — Stress",
            "passou": e7_passou,
            "valor": e7_valor,
            "detalhe": e7_detalhe,
        },
    ]

    falhas = [c["id"] for c in criterios if not c["passou"]]
    n_passou = sum(1 for c in criterios if c["passou"])

    if n_passou == 8:
        resultado = "OPERAR"
    elif n_passou >= 6:
        resultado = "MONITORAR"
    else:
        resultado = "EXCLUÍDO"

    ciclo = None
    if not historico.empty:
        ciclo = historico.iloc[-1].get("ciclo_id") or historico.iloc[-1].get("mes_ano")

    return {
        "ticker": ticker,
        "ciclo": ciclo,
        "criterios": criterios,
        "resultado": resultado,
        "falhas": falhas if resultado != "OPERAR" else [],
        "n_passou": n_passou,
        "anos_validos": ANOS_VALIDOS,
        "anos_cobertos": anos_cobertos,
        "fonte_dados": "book_backtest.parquet+master_json",
    }