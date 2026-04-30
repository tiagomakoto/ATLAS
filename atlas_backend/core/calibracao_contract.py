from __future__ import annotations

from typing import Any, Dict, List


STEP_KEYS: List[str] = ["1_backtest_dados", "2_tune", "3_gate_fire"]
STEP_STATUS: List[str] = ["idle", "running", "done", "error", "paused", "skipped"]

DEFAULT_STEP = {
    "status": "idle",
    "iniciado_em": None,
    "concluido_em": None,
    "erro": None,
}


def _safe_status(value: Any) -> str:
    status = str(value or "idle").lower()
    if status not in STEP_STATUS:
        return "idle"
    return status


def normalize_step_payload(step: Dict[str, Any] | None) -> Dict[str, Any]:
    step = step or {}
    return {
        "status": _safe_status(step.get("status")),
        "iniciado_em": step.get("iniciado_em"),
        "concluido_em": step.get("concluido_em"),
        "erro": step.get("erro"),
    }


def normalize_gate_resultado(payload: Dict[str, Any] | None, ticker: str) -> Dict[str, Any]:
    payload = payload or {}
    criterios = payload.get("criterios") or []
    normalized_criterios = []
    for idx, item in enumerate(criterios, start=1):
        normalized_criterios.append(
            {
                "id": item.get("id") or f"E{idx}",
                "nome": item.get("nome") or f"Critério {idx}",
                "passou": bool(item.get("passou", False)),
                "valor": item.get("valor", "N/D"),
                "detalhe": item.get("detalhe"),
            }
        )

    resultado = str(payload.get("resultado") or "BLOQUEADO").upper()
    if resultado not in {"OPERAR", "BLOQUEADO"}:
        resultado = "BLOQUEADO"

    falhas = payload.get("falhas")
    if not isinstance(falhas, list):
        falhas = [c["id"] for c in normalized_criterios if not c["passou"]]

    return {
        "ticker": ticker,
        "ciclo": payload.get("ciclo"),
        "criterios": normalized_criterios,
        "resultado": resultado,
        "falhas": falhas if resultado != "OPERAR" else [],
    }


def normalize_fire_diagnostico(payload: Dict[str, Any] | None, ticker: str) -> Dict[str, Any]:
    payload = payload or {}
    regimes = payload.get("regimes") or []
    normalized_regimes = []
    for item in regimes:
        normalized_regimes.append(
            {
                "regime": item.get("regime") or "DESCONHECIDO",
                "trades": int(item.get("trades") or 0),
                "wins": int(item.get("wins") or 0),
                "losses": int(item.get("losses") or 0),
                "acerto_pct": float(item.get("acerto_pct") or 0.0),
                "ir": float(item.get("ir") or 0.0),
                "worst_trade": item.get("worst_trade"),
                "best_trade": item.get("best_trade"),
                "avg_win": item.get("avg_win"),
                "avg_loss": item.get("avg_loss"),
                "profit_factor": item.get("profit_factor"),
                "expectancy": item.get("expectancy"),
                "estrategia_dominante": item.get("estrategia_dominante"),
                "estrategias": item.get("estrategias") or [],
                "motivos_saida": item.get("motivos_saida") or {},
            }
        )

    cobertura = payload.get("cobertura") or {}
    return {
        "ticker": ticker,
        "regimes": normalized_regimes,
        "cobertura": {
            "ciclos_com_operacao": int(cobertura.get("ciclos_com_operacao") or 0),
            "total_ciclos": int(cobertura.get("total_ciclos") or 0),
            "total_trades": int(cobertura.get("total_trades") or 0),
            "acerto_geral_pct": float(cobertura.get("acerto_geral_pct") or 0.0),
            "pnl_total": float(cobertura.get("pnl_total") or 0.0),
        },
        "stops_por_regime": payload.get("stops_por_regime") or {},
    }


def normalize_guard_payload(payload: Dict[str, Any] | None, ticker: str) -> Dict[str, Any]:
    payload = payload or {}
    dias = payload.get("dias_desde_atualizacao")
    try:
        dias = int(dias) if dias is not None else None
    except Exception:
        dias = None

    dados_recentes = bool(payload.get("dados_recentes", False))
    if dias is not None:
        dados_recentes = dias < 7

    return {
        "ticker": ticker,
        "data_ultimo_cotahist": payload.get("data_ultimo_cotahist"),
        "dias_desde_atualizacao": dias,
        "dados_recentes": dados_recentes,
        "deve_exibir_guard": dados_recentes,
        "mensagem": "Dados recentes detectados - confirmar execução do step 1" if dados_recentes else "",
    }


def normalize_tune_ranking(
    tune_ranking_estrategia: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Normaliza tune_ranking_estrategia para payload do frontend.

    v3.1: expõe anomalia e aplicacao por regime.
    aguardando_confirmacao_regimes = True apenas se há anomalia pendente de resolução CEO.
    """
    ranking = tune_ranking_estrategia or {}
    meta = ranking.get("_meta") or {}

    regimes_out: Dict[str, Any] = {}
    for regime, dados in ranking.items():
        if regime == "_meta":
            continue
        if not isinstance(dados, dict):
            continue
        eleicao_status = dados.get("eleicao_status", "in_progress")
        ranking_list = dados.get("ranking") or []
        estrategia_eleita = dados.get("estrategia_eleita")
        aplicacao = dados.get("aplicacao")
        anomalia = dados.get("anomalia") or {}
        anomalia_detectada = bool(anomalia.get("detectada", False))
        confirmado = bool(dados.get("confirmado", False))

        # confirmavel = tem anomalia pendente de resolução CEO
        confirmavel = anomalia_detectada and not confirmado
        motivo_bloqueio = None

        if eleicao_status == "bloqueado":
            motivo_bloqueio = "Regime bloqueado - sem estrategia associada"
        elif eleicao_status == "in_progress":
            motivo_bloqueio = "Eleicao em andamento"
        elif not confirmavel and eleicao_status in ("competitiva", "estrutural_fixo"):
            # Aplicado automaticamente ou anomalia já resolvida
            motivo_bloqueio = None
        elif eleicao_status == "estrutural_fixo" and not estrategia_eleita:
            motivo_bloqueio = "Sem estrategia estrutural definida"
        elif eleicao_status == "competitiva" and not (ranking_list and ranking_list[0].get("estrategia")):
            motivo_bloqueio = "Sem estrategia classificada no ranking"

        regimes_out[regime] = {
            "eleicao_status":              eleicao_status,
            "n_trades":                    dados.get("n_trades"),
            "data_eleicao":                dados.get("data_eleicao"),
            "confirmado":                  confirmado,
            "estrategia_eleita":           estrategia_eleita,
            "ranking":                     ranking_list,
            "confirmavel":                 confirmavel,
            "motivo_bloqueio_confirmacao": motivo_bloqueio,
            "aplicacao":                   aplicacao,
            "anomalia":                    {
                "detectada": anomalia_detectada,
                "motivos":   anomalia.get("motivos") or [],
            },
            "status_calibracao":           dados.get("status_calibracao"),
            "tp_calibrado":                dados.get("tp_calibrado"),
            "stop_calibrado":              dados.get("stop_calibrado"),
            "ir_calibrado":                dados.get("ir_calibrado"),
        }

    # Sub-status: aguardando_confirmacao_regimes = há anomalia pendente de resolução CEO
    anomalia_pendente = any(
        v["anomalia"]["detectada"] and not v["confirmado"]
        for v in regimes_out.values()
    )

    return {
        "_meta": {
            "run_id":                meta.get("run_id"),
            "versao":                meta.get("versao"),
            "iniciado_em":           meta.get("iniciado_em"),
            "concluido_em":          meta.get("concluido_em"),
            "trials_por_candidato":  meta.get("trials_por_candidato"),
            "early_stop_patience":   meta.get("early_stop_patience"),
            "startup_trials":        meta.get("startup_trials"),
            "n_minimo_calibracao":   meta.get("n_minimo_calibracao"),
        },
        "regimes":                       regimes_out,
        "aguardando_confirmacao_regimes": anomalia_pendente,
        "concluido":                     meta.get("concluido_em") is not None,
    }


def build_calibracao_payload(
    *,
    ticker: str,
    calibracao: Dict[str, Any] | None,
    guard: Dict[str, Any] | None,
    gate_resultado: Dict[str, Any] | None,
    fire_diagnostico: Dict[str, Any] | None,
    tune_ranking_estrategia: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    calibracao = calibracao or {}
    steps_raw = calibracao.get("steps") or {}

    # Compatibilidade com legado 3_backtest_gate.
    step3_legacy = steps_raw.get("3_backtest_gate")
    step3_current = steps_raw.get("3_gate_fire")

    steps = {
        "1_backtest_dados": normalize_step_payload(steps_raw.get("1_backtest_dados")),
        "2_tune": normalize_step_payload(steps_raw.get("2_tune")),
        "3_gate_fire": normalize_step_payload(step3_current or step3_legacy),
    }

    step_atual = calibracao.get("step_atual")
    try:
        step_atual = int(step_atual)
    except Exception:
        step_atual = None
    if step_atual not in {1, 2, 3}:
        if steps["3_gate_fire"]["status"] in {"running", "done", "error", "paused"}:
            step_atual = 3
        elif steps["2_tune"]["status"] in {"running", "done", "error", "paused"}:
            step_atual = 2
        else:
            step_atual = 1

    gate = normalize_gate_resultado(gate_resultado, ticker)
    fire = normalize_fire_diagnostico(fire_diagnostico, ticker)
    guard_payload = normalize_guard_payload(guard, ticker)
    tune_ranking_payload = normalize_tune_ranking(tune_ranking_estrategia)

    return {
        "ticker": ticker,
        "versao_contrato": "calibracao.v3.0",
        "step_atual": step_atual,
        "steps": steps,
        "step_1_guard": guard_payload,
        "step_2": {
            "id": "2_tune",
            "status": steps["2_tune"]["status"],
            "tune_ranking": tune_ranking_payload,
            "aguardando_confirmacao_regimes": tune_ranking_payload["aguardando_confirmacao_regimes"],
        },
        "step_3": {
            "id": "3_gate_fire",
            "status": steps["3_gate_fire"]["status"],
            "gate_resultado": gate,
            "fire_diagnostico": fire,
        },
        "ultimo_evento_em": calibracao.get("ultimo_evento_em"),
    }
