# atlas_backend/api/routes/delta_chaos.py

import re
from datetime import datetime
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

class OnboardingPayload(BaseModel):
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

@router.post("/onboarding")
async def onboarding(payload: OnboardingPayload):
    """
    Inicia onboarding completo de novo ativo.
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
        from atlas_backend.core.dc_runner import dc_orbit_backtest, dc_tune, dc_gate_backtest

        emit_log(f"[ONBOARDING] Iniciando {ticker}", level="info")

        # Ano dinâmico para ORBIT
        ano_atual = datetime.now().year
        anos_orbit = list(range(2002, ano_atual + 1))
        await dc_orbit_backtest(ticker=ticker, anos=anos_orbit)
        await dc_tune(ticker=ticker)
        await dc_gate_backtest(ticker=ticker)

        emit_log(f"[ONBOARDING] {ticker} concluído", level="info")
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


@router.post("/tune/aplicar")
async def tune_aplicar(payload: dict):
    """
    Aplica parâmetros TUNE aprovados pelo CEO.
    
    Recebe:
        ticker: str
        tp: float (take_profit)
        stop: float (stop_loss)
    
    Retorna:
        status: "ok"
    """
    ticker = payload.get("ticker", "").strip().upper()
    tp = float(payload.get("tp"))
    stop = float(payload.get("stop"))
    
    if not re.match(r"^[A-Z0-9]{4,6}$", ticker):
        raise HTTPException(status_code=400, detail=f"Ticker inválido: {ticker}")
    
    if tp <= 0 or stop <= 0:
        raise HTTPException(status_code=400, detail="TP e STOP devem ser positivos")
    
    try:
        from atlas_backend.core.terminal_stream import emit_log
        from atlas_backend.core.delta_chaos_reader import get_ativo
        from atlas_backend.core.relatorios import marcar_aplicado
        import tempfile
        import json
        import os
        
        # 1. Ler valor anterior do master JSON
        dados = get_ativo(ticker)
        tp_atual = dados.get("take_profit", 0.0)
        stop_atual = dados.get("stop_loss", 0.0)
        valor_anterior = f"TP={tp_atual} STOP={stop_atual}"
        
        # 2. Gravar novos valores com escrita atômica
        path_ativo = Path(get_paths()["config_dir"]) / f"{ticker}.json"
        path_tmp = path_ativo.with_suffix(".tmp")
        
        dados["take_profit"] = tp
        dados["stop_loss"] = stop
        dados["atualizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(path_tmp, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        os.replace(path_tmp, path_ativo)
        
        # 3. Registrar em historico_config[]
        valor_novo = f"TP={tp} STOP={stop}"
        registro = {
            "data": datetime.now().strftime("%Y-%m-%d"),
            "modulo": "TUNE v1.0",
            "parametro": "tune_aplicado",
            "valor_anterior": valor_anterior,
            "valor_novo": valor_novo,
            "motivo": f"TUNE aprovado pelo CEO — TP={tp*100:.1f}% STOP={stop*100:.1f}%"
        }
        
        # Atualizar historico_config no master JSON
        with open(path_ativo, "r", encoding="utf-8") as f:
            dados = json.load(f)
        
        if "historico_config" not in dados:
            dados["historico_config"] = []
        
        dados["historico_config"].append(registro)
        dados["atualizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(path_tmp, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        os.replace(path_tmp, path_ativo)
        
        # 4. Marcar relatório como aplicado (se houver)
        # O ID do relatório é extraído do último registro de TUNE no historico_config
        tunes = [c for c in dados.get("historico_config", []) if "TUNE" in c.get("modulo", "")]
        if tunes:
            # Busca o último relatório não aplicado no index.json
            from atlas_backend.core.relatorios import obter_todos_relatorios
            index = obter_todos_relatorios()
            for rel in reversed(index):
                if (rel.get("ticker") == ticker and 
                    rel.get("tipo") == "TUNE" and 
                    not rel.get("aplicado", False)):
                    marcar_aplicado(rel["id"])
                    break
        
        emit_log(f"[TUNE] {ticker}: parâmetros aplicados — TP={tp*100:.1f}% STOP={stop*100:.1f}%", level="info")
        return {"status": "ok", "ticker": ticker, "tp": tp, "stop": stop}

    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/onboarding/iniciar")
async def onboarding_iniciar(payload: OnboardingPayload):
    """
    Inicia onboarding completo de novo ativo.
    Sequência: backtest_dados → tune → backtest_gate
    Cria/atualiza campo onboarding no master JSON, dispara step 1 via subprocess
    """
    _validar_confirm(payload.confirm, payload.description)
    ticker = payload.ticker.strip().upper()
    
    if not re.match(r"^[A-Z0-9]{4,6}$", ticker):
        raise HTTPException(
            status_code=400,
            detail=f"Ticker inválido: {ticker}"
        )
    
    try:
        from atlas_backend.core.dc_runner import dc_onboarding_iniciar
        result = await dc_onboarding_iniciar(ticker)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/onboarding/{ticker}")
async def onboarding_status(ticker: str):
    """
    Retorna estado atual do onboarding do ativo
    Inclui reconciliação watchdog: se running + ultimo_evento_em > 10min → paused
    Retorna: campo onboarding completo do master JSON
    """
    _validar_ticker(ticker)
    
    try:
        from atlas_backend.core.delta_chaos_reader import get_ativo
        from datetime import datetime, timedelta
        
        dados = get_ativo(ticker)
        onboarding = dados.get("onboarding", {})
        
        # Reconciliação watchdog: se running e ultimo_evento_em > 10min → paused
        if onboarding.get("step_atual") and onboarding.get("steps"):
            for step_key, step_info in onboarding["steps"].items():
                if step_info.get("status") == "running":
                    ultimo_evento = onboarding.get("ultimo_evento_em")
                    if ultimo_evento:
                        ultimo_dt = datetime.fromisoformat(ultimo_evento)
                        if datetime.now() - ultimo_dt > timedelta(minutes=10):
                            # Atualizar para paused
                            step_info["status"] = "paused"
                            onboarding["ultimo_evento_em"] = datetime.now().isoformat()
                            
                            # Atualizar no arquivo com escrita atômica
                            path_ativo = Path(get_paths()["config_dir"]) / f"{ticker}.json"
                            path_tmp = path_ativo.with_suffix(".tmp")
                            
                            with open(path_tmp, "w", encoding="utf-8") as f:
                                json.dump(dados, f, indent=2, ensure_ascii=False)
                            os.replace(path_tmp, path_ativo)
                            
                            # Atualizar dados locais
                            dados["onboarding"] = onboarding
        
        return onboarding
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/onboarding/{ticker}/retomar")
async def onboarding_retomar(ticker: str):
    """
    Retoma onboarding do step atual (usado quando status == "paused")
    Para step 2: Optuna continua do SQLite existente
    Retorna: { "status": "resumed", "step": N }
    """
    _validar_ticker(ticker)
    
    try:
        from atlas_backend.core.dc_runner import dc_onboarding_retomar
        result = await dc_onboarding_retomar(ticker)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/onboarding/{ticker}/progresso-tune")
async def onboarding_progresso_tune(ticker: str):
    """
    Lê tune_{TICKER}.db via conexão read-only
    Retorna: { "trials_completos": N, "trials_total": 200, "best_ir": X }
    Conexão deve ser read-only explícita para evitar conflito com processo de escrita
    """
    _validar_ticker(ticker)
    
    try:
        from atlas_backend.core.dc_runner import dc_onboarding_progresso_tune
        result = await dc_onboarding_progresso_tune(ticker)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))