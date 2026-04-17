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
                "acerto_pct": float(item.get("acerto_pct") or 0.0),
                "ir": float(item.get("ir") or 0.0),
                "worst_trade": item.get("worst_trade"),
                "estrategia_dominante": item.get("estrategia_dominante"),
            }
        )

    cobertura = payload.get("cobertura") or {}
    return {
        "ticker": ticker,
        "regimes": normalized_regimes,
        "cobertura": {
            "ciclos_com_operacao": int(cobertura.get("ciclos_com_operacao") or 0),
            "total_ciclos": int(cobertura.get("total_ciclos") or 0),
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


def build_calibracao_payload(
    *,
    ticker: str,
    calibracao: Dict[str, Any] | None,
    guard: Dict[str, Any] | None,
    gate_resultado: Dict[str, Any] | None,
    fire_diagnostico: Dict[str, Any] | None,
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

    return {
        "ticker": ticker,
        "versao_contrato": "calibracao.v3.0",
        "step_atual": step_atual,
        "steps": steps,
        "step_1_guard": guard_payload,
        "step_3": {
            "id": "3_gate_fire",
            "status": steps["3_gate_fire"]["status"],
            "gate_resultado": gate,
            "fire_diagnostico": fire,
        },
        "ultimo_evento_em": calibracao.get("ultimo_evento_em"),
    }
