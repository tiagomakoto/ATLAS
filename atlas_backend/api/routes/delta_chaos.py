# atlas_backend/api/routes/delta_chaos.py

import re
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
from atlas_backend.core.dc_runner import (
    dc_eod, dc_orbit_backtest, dc_tune, dc_gate_backtest,
    dc_reflect_daily, dc_orbit_update, dc_gate_eod,
    dc_gate_backtest, dc_daily
)
from atlas_backend.core.delta_chaos_reader import list_ativos, get_ativo, update_ativo
from atlas_backend.core.paths import get_paths
from atlas_backend.core.relatorios import gerar_relatorio, marcar_aplicado
from atlas_backend.core.calibracao_contract import (
    build_calibracao_payload,
    normalize_gate_resultado,
    normalize_fire_diagnostico,
    normalize_guard_payload,
    normalize_tune_ranking,
)
from atlas_backend.core.delta_chaos_reader import (
    get_ativo_raw,
    get_cotahist_recente_info,
    get_gate_resultado,
    get_fire_diagnostico,
    sanitize_record,
)

router = APIRouter(prefix="/delta-chaos", tags=["delta-chaos"])

# ── Schemas ───────────────────────────────────────────────────────

class EodPayload(BaseModel):
    xlsx_dir: Optional[str] = None
    confirm: bool = False
    description: str = ""

class TickerPayload(BaseModel):
    ticker: str
    confirm: bool = False
    description: str = ""
    anos: Optional[List[int]] = None

class CalibracaoPayload(BaseModel):
    ticker: str
    confirm: bool = False
    description: str = ""

# ── Validações comuns ─────────────────────────────────────────────

def _validar_confirm(confirm: bool, description: str):
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="CONFIRMATION_REQUIRED — envie confirm=true"
        )
    if not description.strip():
        raise HTTPException(
            status_code=400,
            detail="DESCRIPTION_REQUIRED — descrição obrigatória"
        )

def _validar_ticker(ticker: str):
    ativos = list_ativos()
    if ticker not in ativos:
        raise HTTPException(
            status_code=404,
            detail=f"Ativo '{ticker}' não encontrado nos ativos parametrizados"
        )

def _resolver_xlsx_dir(xlsx_dir: Optional[str]) -> str:
    if xlsx_dir:
        return xlsx_dir
    paths = get_paths()
    base = paths.get("delta_chaos_base")
    if not base:
        raise HTTPException(
            status_code=503,
            detail="delta_chaos_base ausente no paths.json"
        )
    default = str(Path(base) / "opcoes_hoje")
    return default

# ── Endpoints ─────────────────────────────────────────────────────

@router.post("/eod/executar")
async def eod_executar(payload: EodPayload):
    """
    Estágio 2 — executa EOD completo para os ativos aprovados.
    Requer confirm=true e description.
    Deve ser chamado somente após /eod/preview ter sido exibido.
    """
    _validar_confirm(payload.confirm, payload.description)
    xlsx_dir = _resolver_xlsx_dir(payload.xlsx_dir)
    try:
        result = await dc_eod(xlsx_dir=xlsx_dir)
        return {"status": result["status"], "output": result["output"]}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orbit")
async def orbit(payload: TickerPayload):
    """
    Roda ORBIT para o ticker informado.
    """
    _validar_confirm(payload.confirm, payload.description)
    _validar_ticker(payload.ticker)
    try:
        result = await dc_orbit_backtest(
            ticker=payload.ticker,
            anos=payload.anos
        )
        return {"status": result["status"], "output": result["output"]}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tune")
async def tune(payload: TickerPayload):
    """
    Roda TUNE para o ticker informado.
    Calcula e registra — não aplica automaticamente.
    Gera relatório .md em relatorios/ e atualiza index.json.
    """
    _validar_confirm(payload.confirm, payload.description)
    _validar_ticker(payload.ticker)
    try:
        result = await dc_tune(ticker=payload.ticker)
        
        if result.get("status") == "OK":
            # Gerar relatório após TUNE bem-sucedido
            from atlas_backend.core.relatorios import gerar_relatorio
            from atlas_backend.core.delta_chaos_reader import get_ativo
            from datetime import date
            
            dados = get_ativo(payload.ticker)
            historico = dados.get("historico", [])
            ciclo = historico[-1].get("ciclo_id", date.today().strftime("%Y-%m")) if historico else date.today().strftime("%Y-%m")
            
            tp_atual = dados.get("take_profit", 0.0)
            stop_atual = dados.get("stop_loss", 0.0)
            
            # Extrair valores sugeridos do output do TUNE
            output = result.get("output", "")
            import re
            match = re.search(r"TP=([\d.]+)\s+STOP=([\d.]+)", output)
            if match:
                tp_sugerido = float(match.group(1))
                stop_sugerido = float(match.group(2))
            else:
                tp_sugerido = tp_atual
                stop_sugerido = stop_atual
            
            delta_tp = tp_sugerido - tp_atual
            delta_stop = stop_sugerido - stop_atual
            
            # Determinar recomendação baseada no delta
            if abs(delta_tp) < 0.05 and abs(delta_stop) < 0.1:
                recomendacao = "MANTER"
            elif delta_tp > 0 and delta_stop > 0:
                recomendacao = "APLICAR"
            else:
                recomendacao = "REVISAR"
            
            params = {
                "tp_atual": tp_atual,
                "stop_atual": stop_atual,
                "tp_sugerido": tp_sugerido,
                "stop_sugerido": stop_sugerido,
                "delta_tp": delta_tp,
                "delta_stop": delta_stop,
                "recomendacao": recomendacao,
                "detalhes": {}
            }
            
            relatorio = gerar_relatorio(
                ticker=payload.ticker,
                ciclo=ciclo,
                tipo="TUNE",
                params=params
            )
            
            return {
                "status": "OK",
                "output": result.get("output", ""),
                "relatorio": relatorio
            }
        
        return {"status": result.get("status"), "output": result.get("output")}
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gate")
async def gate(payload: TickerPayload):
    """
    Roda GATE completo para o ticker informado.
    """
    _validar_confirm(payload.confirm, payload.description)
    _validar_ticker(payload.ticker)
    try:
        result = await dc_gate_backtest(ticker=payload.ticker)
        return {
            "status": result["status"],
            "output": result["output"],
            "returncode": result["returncode"]
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calibracao")
async def calibracao(payload: CalibracaoPayload):
    """
    Inicia calibração completa de novo ativo.
    Sequência: TAPE → ORBIT → TUNE → GATE
    Cada etapa roda em sequência via dc_runner.
    """
    _validar_confirm(payload.confirm, payload.description)
    ticker = payload.ticker.strip().upper()

    if not re.match(r"^[A-Z0-9]{4,6}$", ticker):
        raise HTTPException(
            status_code=400,
            detail=f"Ticker inválido: {ticker}"
        )

    try:
        from atlas_backend.core.terminal_stream import emit_log
        from atlas_backend.core.dc_runner import dc_orbit_backtest, dc_tune, dc_gate_backtest, dc_fire_diagnostico

        emit_log(f"[CALIBRAÇÃO] Iniciando {ticker}", level="info")

        # Ano dinâmico para ORBIT
        ano_atual = datetime.now(tz=ZoneInfo('America/Sao_Paulo')).year
        anos_orbit = list(range(2002, ano_atual + 1))
        await dc_orbit_backtest(ticker=ticker, anos=anos_orbit)
        await dc_tune(ticker=ticker)
        gate_result = await dc_gate_backtest(ticker=ticker)
        if gate_result.get("status") == "OK" and gate_result.get("gate_resultado", {}).get("resultado") == "OPERAR":
            await dc_fire_diagnostico(ticker=ticker)

        emit_log(f"[CALIBRAÇÃO] {ticker} concluído", level="info")
        return {"status": "OK", "ticker": ticker}

    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/daily/run")
async def daily_run(payload: dict):
    """
    Gerente de Integridade de Dados - v2.6 (refatorado conforme SPEC)
    Ciclo de manutenção ativo: fluxo diário + mensal conforme SPEC
    """
    from atlas_backend.core.dc_runner import dc_daily

    tickers = list_ativos()
    if not tickers:
        return {"status": "OK", "digest": {}, "eventos": [], "output": "Nenhum ativo para processar"}

    result = await dc_daily(tickers)
    
    # ═══ NOVO: Extrair digest e eventos do resultado ═══
    return {
        "status": "OK",
        "digest": result.get("digest", result),
        "eventos": result.get("eventos", []),
        "output": f"Processados {len(result.get('digest', result))} ativos"
    }
    # ═══ FIM NOVO ═══


@router.post("/tune/confirmar-regime")
async def tune_confirmar_regime(payload: dict):
    """
    DEPRECADO (TUNE v3.1) — substituído por aplicação automática + confirmar-regime-anomalia.
    Retorna 410 Gone.
    """
    raise HTTPException(
        status_code=410,
        detail=(
            "Endpoint deprecado em TUNE v3.1. "
            "Regimes sem anomalia são aplicados automaticamente pelo TUNE. "
            "Para resolver anomalias use POST /delta-chaos/tune/confirmar-regime-anomalia."
        ),
    )


@router.post("/tune/confirmar-regime-anomalia")
async def tune_confirmar_regime_anomalia(payload: dict):
    """
    Resolve anomalia detectada pelo TUNE v3.1 para um regime específico.

    Recebe: { ticker, regime, run_id, acao: "aplicar" | "rejeitar" }
    - aplicar: grava estrategias[regime] + tp_por_regime[regime] + stop_por_regime[regime].
    - rejeitar: mantém parâmetros do ciclo anterior (não grava nada no ativo operacional).
    Em ambos os casos marca confirmado=True e registra em historico_config.
    Rejeita se regime não tem anomalia detectada, se run_id inválido ou se já confirmado.
    """
    ticker = str(payload.get("ticker") or "").strip().upper()
    regime = str(payload.get("regime") or "").strip()
    _run_id_raw = payload.get("run_id")
    run_id = str(_run_id_raw).strip() if _run_id_raw is not None else ""
    acao   = str(payload.get("acao") or "").strip().lower()

    if not re.match(r"^[A-Z0-9]{4,6}$", ticker):
        raise HTTPException(status_code=400, detail=f"Ticker inválido: {ticker}")
    if not regime:
        raise HTTPException(status_code=400, detail="regime obrigatório")
    if not run_id:
        raise HTTPException(status_code=400, detail="run_id obrigatório")
    if acao not in {"aplicar", "rejeitar"}:
        raise HTTPException(status_code=400, detail="acao deve ser 'aplicar' ou 'rejeitar'")

    try:
        import tempfile
        from atlas_backend.core.terminal_stream import emit_log
        from delta_chaos.tune import _aplicar_regime_no_ativo

        path_ativo = Path(get_paths()["config_dir"]) / f"{ticker}.json"
        with open(path_ativo, "r", encoding="utf-8") as f:
            dados = json.load(f)

        ranking_root = dados.get("tune_ranking_estrategia") or {}
        meta = ranking_root.get("_meta") or {}

        if meta.get("run_id") != run_id:
            raise HTTPException(status_code=409, detail="run_id não corresponde ao ranking atual")

        regime_dados = ranking_root.get(regime)
        if regime_dados is None:
            raise HTTPException(status_code=404, detail=f"Regime {regime} não encontrado no ranking")

        if regime_dados.get("confirmado"):
            raise HTTPException(status_code=409, detail=f"Regime {regime} já confirmado")

        anomalia = regime_dados.get("anomalia") or {}
        if not anomalia.get("detectada"):
            raise HTTPException(
                status_code=400,
                detail=f"Regime {regime} não tem anomalia detectada — não requer confirmação CEO",
            )

        agora = datetime.now(tz=ZoneInfo('America/Sao_Paulo')).strftime("%Y-%m-%d %H:%M:%S")
        motivos = anomalia.get("motivos") or []

        if not isinstance(dados.get("historico_config"), list):
            dados["historico_config"] = []

        if acao == "aplicar":
            _aplicar_regime_no_ativo(dados, regime, regime_dados, run_id, "anomalia_aprovada_ceo")
            regime_dados["aplicacao"] = "anomalia_aprovada_ceo"
            regime_dados["confirmado"] = True
            dados["historico_config"].append({
                "data":     agora[:10],
                "modulo":   "TUNE v3.1",
                "parametro": f"anomalia.{regime}",
                "valor_novo": "aprovada_ceo",
                "motivo":   f"Anomalia aprovada CEO — motivos={motivos} run_id={run_id}",
            })
        else:
            regime_dados["aplicacao"] = "anomalia_rejeitada_ceo"
            regime_dados["confirmado"] = True
            dados["historico_config"].append({
                "data":     agora[:10],
                "modulo":   "TUNE v3.1",
                "parametro": f"anomalia.{regime}",
                "valor_novo": "rejeitada_ceo",
                "motivo":   f"Anomalia rejeitada CEO — parâmetros do ciclo anterior mantidos — motivos={motivos} run_id={run_id}",
            })

        ranking_root[regime]             = regime_dados
        dados["tune_ranking_estrategia"] = ranking_root
        dados["atualizado_em"]           = agora

        tmp_fd, tmp_path = tempfile.mkstemp(dir=path_ativo.parent, suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, path_ativo)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

        estrategia      = regime_dados.get("estrategia_eleita")
        status_calibracao = regime_dados.get("status_calibracao")  # "calibrado" | "fallback_global" | None
        emit_log(
            f"[TUNE v3.1] {ticker} {regime}: anomalia {acao} → {estrategia}",
            level="info",
        )
        from atlas_backend.core.event_bus import emit_dc_event
        emit_dc_event(
            "dc_tune_anomalia_resolvida", "TUNE", "ok",
            ticker=ticker, regime=regime, acao=acao,
        )
        return {
            "status":           "ok",
            "ticker":           ticker,
            "regime":           regime,
            "acao":             acao,
            "estrategia":       estrategia,
            "status_calibracao": status_calibracao,
        }

    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tune/confirmar-todos")
async def tune_confirmar_todos(payload: dict):
    """
    DEPRECADO (TUNE v3.1) — substituído por aplicação automática + confirmar-regime-anomalia.
    Retorna 410 Gone.
    """
    raise HTTPException(
        status_code=410,
        detail=(
            "Endpoint deprecado em TUNE v3.1. "
            "Regimes sem anomalia são aplicados automaticamente pelo TUNE. "
            "Para resolver anomalias use POST /delta-chaos/tune/confirmar-regime-anomalia."
        ),
    )


@router.post("/calibracao/iniciar")
async def calibracao_iniciar(payload: CalibracaoPayload):
    """
    Inicia calibração completa de novo ativo.
    Sequência: backtest_dados → tune → backtest_gate
    Cria/atualiza campo calibracao no master JSON, dispara step 1 via subprocess
    """
    _validar_confirm(payload.confirm, payload.description)
    ticker = payload.ticker.strip().upper()
    
    if not re.match(r"^[A-Z0-9]{4,6}$", ticker):
        raise HTTPException(
            status_code=400,
            detail=f"Ticker inválido: {ticker}"
        )
    
    try:
        from atlas_backend.core.dc_runner import dc_calibracao_iniciar
        result = await dc_calibracao_iniciar(ticker)
        return {
            "versao_contrato": "calibracao.v3.0",
            "ticker": ticker,
            "status": result.get("status", "started"),
            "step_atual": int(result.get("step", 1)),
            "steps": {
                "1_backtest_dados": {"status": "idle", "iniciado_em": None, "concluido_em": None, "erro": None},
                "2_tune": {"status": "idle", "iniciado_em": None, "concluido_em": None, "erro": None, "trials_completos": 0, "trials_total": 150},
                "3_gate_fire": {"status": "idle", "iniciado_em": None, "concluido_em": None, "erro": None},
            },
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calibracao/{ticker}")
async def calibracao_status(ticker: str):
    """
    Retorna estado atual da calibração do ativo
    Inclui reconciliação watchdog: se running + ultimo_evento_em > 10min → paused
    Retorna: campo calibracao completo do master JSON
    """
    _validar_ticker(ticker)
    
    try:
        from datetime import datetime, timedelta, timezone
        from atlas_backend.core.timeutils import iso_utc

        dados = get_ativo(ticker)
        dados_raw = get_ativo_raw(ticker)
        calibracao = (dados_raw.get("calibracao") or {}).copy()

        # Reconciliação watchdog: se running e ultimo_evento_em > 10min → paused
        if calibracao.get("step_atual") and calibracao.get("steps"):
            for step_key, step_info in calibracao["steps"].items():
                if step_info.get("status") == "running":
                    ultimo_evento = calibracao.get("ultimo_evento_em")
                    if ultimo_evento:
                        ultimo_dt = datetime.fromisoformat(ultimo_evento)
                        # Garantir comparação entre aware datetimes (timestamps
                        # podem ser naive-local legados ou UTC+00:00 novos).
                        if ultimo_dt.tzinfo is None:
                            ultimo_dt = ultimo_dt.replace(tzinfo=timezone.utc)
                        if datetime.now(timezone.utc) - ultimo_dt > timedelta(minutes=10):
                            # Atualizar para paused
                            step_info["status"] = "paused"
                            calibracao["ultimo_evento_em"] = iso_utc()
                            
                            # Atualizar no arquivo com escrita atômica
                            path_ativo = Path(get_paths()["config_dir"]) / f"{ticker}.json"
                            path_tmp = path_ativo.with_suffix(".tmp")
                            
                            dados_raw["calibracao"] = calibracao
                            with open(path_tmp, "w", encoding="utf-8") as f:
                                json.dump(dados_raw, f, indent=2, ensure_ascii=False)
                            os.replace(path_tmp, path_ativo)
                            
                            # Atualizar dados locais
                            dados["calibracao"] = calibracao

        guard = normalize_guard_payload(get_cotahist_recente_info(ticker), ticker)
        # Usa exclusivamente o dado persistido em calibracao.gate_resultado —
        # nunca recomputa via gate_helper/book_backtest.parquet, pois uma nova
        # calibração em andamento reseta esse campo para null e não deve mostrar
        # resultados de runs anteriores.
        gate_stored = calibracao.get("gate_resultado")
        gate = normalize_gate_resultado(gate_stored, ticker)
        fire_stored = calibracao.get("fire_diagnostico")
        fire = normalize_fire_diagnostico(fire_stored, ticker)
        tune_ranking = dados_raw.get("tune_ranking_estrategia")

        return build_calibracao_payload(
            ticker=ticker,
            calibracao=calibracao,
            guard=guard,
            gate_resultado=gate,
            fire_diagnostico=fire,
            tune_ranking_estrategia=tune_ranking,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calibracao/{ticker}/retomar")
async def calibracao_retomar(ticker: str):
    """
    Retoma calibração do step atual (usado quando status == "paused")
    Para step 2: Optuna continua do SQLite existente
    Retorna: { "status": "resumed", "step": N }
    """
    _validar_ticker(ticker)
    
    try:
        from atlas_backend.core.dc_runner import dc_calibracao_retomar
        result = await dc_calibracao_retomar(ticker)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calibracao/{ticker}/progresso-tune")
async def calibracao_progresso_tune(ticker: str):
    """
    Lê tune_{TICKER}.db via conexão read-only
    Retorna: { "trials_completos": N, "trials_total": <config.tune.trials_por_candidato>, "best_ir": X }
    Conexão deve ser read-only explícita para evitar conflito com processo de escrita
    """
    _validar_ticker(ticker)

    try:
        from atlas_backend.core.dc_runner import dc_calibracao_progresso_tune
        result = await dc_calibracao_progresso_tune(ticker)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calibracao/{ticker}/exportar-relatorio")
async def calibracao_exportar_relatorio(ticker: str):
    """
    Retorna dados atuais de calibração do ticker para o frontend gerar o .md client-side.
    Não grava nenhum arquivo em disco.

    Retorna:
    {
        "status": "ok",
        "gate_resultado": {...},
        "fire_diagnostico": {...},
        "steps": {...},
        "data": "2026-04-17"
    }
    """
    _validar_ticker(ticker)

    try:
        from atlas_backend.core.relatorios import exportar_relatorio_calibracao

        result = exportar_relatorio_calibracao(ticker)

        if "erro" in result:
            raise HTTPException(status_code=400, detail=result["erro"])

        return {
            "status": "ok",
            "gate_resultado": result.get("gate_resultado"),
            "fire_diagnostico": result.get("fire_diagnostico"),
            "steps": result.get("steps"),
            "data": result.get("data"),
            "tune_stats": result.get("tune_stats"),
            "gate_stats": result.get("gate_stats"),
            "tune_ranking_estrategia": result.get("tune_ranking_estrategia"),
        }
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ativos/{ticker}/historico-config")
async def get_historico_config(ticker: str):
    """
    Retorna o array completo de historico_config do master JSON do ativo,
    ordenado por data decrescente (mais recente primeiro).
    """
    _validar_ticker(ticker)
    try:
        raw = get_ativo_raw(ticker)
        entries = raw.get("historico_config", [])
        if not isinstance(entries, list):
            entries = []
        sanitized = [sanitize_record(e) for e in entries if isinstance(e, dict)]
        sanitized.sort(key=lambda e: str(e.get("data") or ""), reverse=True)
        return {"ticker": ticker, "historico_config": sanitized}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


