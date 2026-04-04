# atlas_backend/api/routes/delta_chaos.py

import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from atlas_backend.core.dc_runner import (
    run_eod_preview, run_eod,
    run_orbit, run_tune, run_gate,
    run_reflect_daily, run_orbit_update, run_gate_eod,
    run_backtest_gate
)
from atlas_backend.core.delta_chaos_reader import list_ativos, get_ativo
from atlas_backend.core.paths import get_paths
from atlas_backend.core.event_bus import emit_dc_event
from pathlib import Path
import pandas as pd
import json
import os
from datetime import datetime, date

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

@router.post("/eod/preview")
async def eod_preview(payload: EodPayload):
    """
    Estágio 1 — verifica quais ativos serão processados no EOD.
    Não executa nada. O operador vê o resultado e decide se avança.
    """
    xlsx_dir = _resolver_xlsx_dir(payload.xlsx_dir)
    try:
        result = await run_eod_preview(xlsx_dir=xlsx_dir)
        return {"status": result["status"], "output": result["output"]}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        result = await run_eod(xlsx_dir=xlsx_dir)
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
        result = await run_orbit(
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
    """
    _validar_confirm(payload.confirm, payload.description)
    _validar_ticker(payload.ticker)
    try:
        result = await run_tune(ticker=payload.ticker)
        return {"status": result["status"], "output": result["output"]}
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
        result = await run_gate(ticker=payload.ticker)
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

    import re
    if not re.match(r"^[A-Z0-9]{4,6}$", ticker):
        raise HTTPException(
            status_code=400,
            detail=f"Ticker inválido: {ticker}"
        )

    try:
        from atlas_backend.core.dc_runner import run_orbit, run_tune, run_gate
        from atlas_backend.core.terminal_stream import emit_log

        emit_log(f"[ONBOARDING] Iniciando {ticker}", level="info")

        # Ano dinÃ¢mico para ORBIT
        ano_atual = datetime.now().year
        anos_orbit = list(range(2002, ano_atual + 1))
        await run_orbit(ticker=ticker, anos=anos_orbit)
        await run_tune(ticker=ticker)
        await run_gate(ticker=ticker)

        emit_log(f"[ONBOARDING] {ticker} concluído", level="info")
        return {"status": "OK", "ticker": ticker}

    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orchestrator/run")
async def orchestrator_run(payload: dict):
    """
    Gerente de Integridade de Dados - v2.6
    Ciclo de manutenção ativo:流程 diário + mensal conforme SPEC ATLAS v2.6
    """
    from atlas_backend.core.terminal_stream import emit_log

    emit_log("[ORQUESTRADOR] 🚀 Iniciando ciclo de manutenção...", level="info")

    try:
        from datetime import timedelta
        from atlas_backend.core.dc_runner import run_backtest_gate

        paths = get_paths()
        ativos = list_ativos()
        if not ativos:
            emit_log("[ORQUESTRADOR] Nenhum ativo parametrizado encontrado", level="warning")
            return {"status": "OK", "output": "Nenhum ativo para processar", "manutencao": []}

        delta_chaos_base = paths.get("delta_chaos_base")
        if not delta_chaos_base:
            raise ValueError("delta_chaos_base ausente no paths.json")

        opcoes_hoje_dir = os.path.join(delta_chaos_base, "opcoes_hoje")
        ohlcv_dir = paths.get("ohlcv_dir")
        book_dir = paths.get("book_dir")

        emit_log(f"[ORQUESTRADOR] Verificando {len(ativos)} ativos...", level="info")

        digest = []
        eventos_ativos = []

        for ticker in ativos:
            emit_log(f"[ORQUESTRADOR] Processando {ticker}...", level="info")

            evento_ativo = {
                "type": "orchestrator_ativo_result",
                "ticker": ticker,
                "ciclo_novo": False,
                "reflect_daily": None,
                "posicao": None,
                "gate_eod": None,
                "bloco_mensal": None,
                "erros": []
            }
            erros_ativo = []

            # === DIÁRIO ===
            # 1. tape_reflect_daily
            xlsx_path = os.path.join(opcoes_hoje_dir, f"{ticker}.xlsx")
            if os.path.exists(xlsx_path):
                try:
                    await run_reflect_daily(ticker, xlsx_path)
                    evento_ativo["reflect_daily"] = "ok"
                except Exception as e:
                    evento_ativo["reflect_daily"] = f"erro: {str(e)}"
                    erros_ativo.append(f"reflect_daily: {str(e)}")
            else:
                evento_ativo["reflect_daily"] = "pulado — sem xlsx"

            # 2. Verificar posição aberta
            book_path = os.path.join(book_dir, "book_paper.json")
            posicao_aberta = None
            if os.path.exists(book_path):
                try:
                    with open(book_path, encoding="utf-8") as f:
                        book_data = json.load(f)
                    ops = book_data.get("ops", [])
                    for op in ops:
                        if op.get("core", {}).get("ativo") == ticker and op.get("core", {}).get("data_saida") is None:
                            premio_entrada = op.get("legs", [{}])[0].get("premio_entrada")
                            if premio_entrada:
                                dados_ativo = get_ativo(ticker)
                                take_profit = dados_ativo.get("take_profit")
                                stop_loss = dados_ativo.get("stop_loss")
                                preco_atual = None
                                if os.path.exists(xlsx_path):
                                    try:
                                        df = pd.read_excel(xlsx_path)
                                        if "fechamento" in df.columns:
                                            preco_atual = df["fechamento"].iloc[-1]
                                    except:
                                        pass
                                if preco_atual and take_profit and stop_loss:
                                    pnl_pct = ((preco_atual - premio_entrada) / premio_entrada) * 100
                                    if pnl_pct >= take_profit or pnl_pct <= -stop_loss:
                                        posicao_aberta = {
                                            "aberta": True,
                                            "pnl_atual": round(pnl_pct, 2),
                                            "acao": "fechada"
                                        }
                                        evento_ativo["posicao"] = posicao_aberta
                                        emit_log(f"[ORQUESTRADOR] {ticker}: posição fechada por TP/STOP (P&L {pnl_pct:.2f}%)", level="info")
                                        break
                                    else:
                                        posicao_aberta = {
                                            "aberta": True,
                                            "pnl_atual": round(pnl_pct, 2),
                                            "acao": "mantida"
                                        }
                                        emit_log(f"[ORQUESTRADOR] {ticker}: posição mantida (P&L {pnl_pct:.2f}%)", level="info")
                except Exception as e:
                    erros_ativo.append(f"book_paper: {str(e)}")

            if posicao_aberta is None:
                evento_ativo["posicao"] = {"aberta": False, "acao": "sem_posicao"}

            # 3. gate_eod
            try:
                gate_eod_result = await run_gate_eod(ticker)
                resultado = gate_eod_result.get("output", "")
                if "OPERAR" in resultado:
                    evento_ativo["gate_eod"] = "OPERAR"
                    emit_log(f"[ORQUESTRADOR] {ticker}: gate_eod = OPERAR (aguarda CEO)", level="info")
                elif "MONITORAR" in resultado:
                    evento_ativo["gate_eod"] = "MONITORAR"
                    emit_log(f"[ORQUESTRADOR] {ticker}: gate_eod = MONITORAR", level="info")
                elif "BLOQUEADO" in resultado:
                    evento_ativo["gate_eod"] = "BLOQUEADO"
                    emit_log(f"[ORQUESTRADOR] {ticker}: gate_eod = BLOQUEADO", level="info")
                else:
                    evento_ativo["gate_eod"] = resultado
            except Exception as e:
                evento_ativo["gate_eod"] = f"erro: {str(e)}"
                erros_ativo.append(f"gate_eod: {str(e)}")

            if evento_ativo["posicao"].get("aberta") or evento_ativo["gate_eod"] in ["MONITORAR", "BLOQUEADO"]:
                eventos_ativos.append(evento_ativo)
                emit_log(f"[ORQUESTRADOR] {ticker}: fim do fluxo diário", level="info")
                # PAUSE
                emit_log(f"[PAUSE] Aguardando 30 segundos antes do próximo ativo...", level="info")
                await asyncio.sleep(30)
                continue

            # === MENSAL ===
            # Detecção de ciclo mudou
            ciclo_mudou = False
            ultimo_ciclo = None
            ohlcv_month = None
            try:
                parquet_path = os.path.join(ohlcv_dir, f"{ticker}.parquet")
                if os.path.exists(parquet_path):
                    df = pd.read_parquet(parquet_path)
                    ohlcv_date = df.index.max()
                    ohlcv_month = ohlcv_date.strftime("%Y-%m")
                    dados_ativo = get_ativo(ticker)
                    if dados_ativo.get("historico") and len(dados_ativo["historico"]) > 0:
                        ultimo_ciclo = dados_ativo["historico"][-1].get("ciclo_id")
                        if ultimo_ciclo:
                            ciclo_mudou = ohlcv_month > ultimo_ciclo
                            evento_ativo["ciclo_novo"] = ciclo_mudou
            except Exception as e:
                erros_ativo.append(f"ciclo_detect: {str(e)}")

            if not ciclo_mudou:
                emit_log(f"[ORQUESTRADOR] {ticker}: ciclo não mudou, bloco mensal pulado", level="info")
                eventos_ativos.append(evento_ativo)
                # PAUSE
                emit_log(f"[PAUSE] Aguardando 30 segundos antes do próximo ativo...", level="info")
                await asyncio.sleep(30)
                continue

            # Bloco mensal
            emit_log(f"[ORQUESTRADOR] {ticker}: ciclo mudou — executando bloco mensal", level="info")
            bloco_mensal = {
                "orbit": None,
                "reflect_cycle": None,
                "gate": None,
                "gate_resultado": None,
                "status_anterior": None,
                "status_novo": None,
                "tune": None
            }

            # 4. run_orbit_update
            status_antes = None
            try:
                status_antes = get_ativo(ticker).get("status")
                await run_orbit_update(ticker)
                bloco_mensal["orbit"] = "ok"
                emit_log(f"[ORQUESTRADOR] {ticker}: orbit update ok", level="info")
            except Exception as e:
                bloco_mensal["orbit"] = f"erro: {str(e)}"
                erros_ativo.append(f"orbit: {str(e)}")
                evento_ativo["erros"] = erros_ativo
                evento_ativo["bloco_mensal"] = bloco_mensal
                eventos_ativos.append(evento_ativo)
                await asyncio.sleep(30)
                continue

            # 5. tape_reflect_cycle (já chamado dentro de --modo orbit)
            bloco_mensal["reflect_cycle"] = "ok"

            # 6. run_backtest_gate
            try:
                await run_backtest_gate(ticker)
                status_depois = get_ativo(ticker).get("status")
                bloco_mensal["gate"] = "ok"
                bloco_mensal["status_anterior"] = status_antes
                bloco_mensal["status_novo"] = status_depois
                emit_log(f"[ORQUESTRADOR] {ticker}: gate ok — {status_antes} → {status_depois}", level="info")
                if status_antes != status_depois:
                    emit_dc_event("status_transition", "ORQUESTRADOR", status="ok",
                                  ticker=ticker, status_anterior=status_antes, status_novo=status_depois,
                                  ciclo=ohlcv_month)
            except Exception as e:
                erro_msg = str(e)
                bloco_mensal["gate"] = f"erro: {erro_msg}"
                erros_ativo.append(f"gate: {erro_msg}")
                emit_log(f"[ORQUESTRADOR] {ticker}: gate erro — {erro_msg}", level="error")

            # 7. TUNE elegível?
            try:
                dados_ativo = get_ativo(ticker)
                historico_config = dados_ativo.get("historico_config", [])
                tunes = [c["data"] for c in historico_config if "TUNE" in c.get("modulo", "")]
                if tunes:
                    from pandas import bdate_range
                    last_tune = max(tunes)
                    dias_uteis = len(bdate_range(last_tune, date.today()))
                    if dias_uteis >= 126:
                        await run_tune(ticker)
                        bloco_mensal["tune"] = "executado"
                        emit_log(f"[ORQUESTRADOR] {ticker}: TUNE executado", level="info")
                    else:
                        bloco_mensal["tune"] = f"pulado — {dias_uteis} dias úteis"
                else:
                    bloco_mensal["tune"] = "pulado — sem histórico"
            except Exception as e:
                erros_ativo.append(f"tune: {str(e)}")
                bloco_mensal["tune"] = f"erro: {str(e)}"

            evento_ativo["bloco_mensal"] = bloco_mensal
            evento_ativo["erros"] = erros_ativo
            eventos_ativos.append(evento_ativo)

            # PAUSE
            emit_log(f"[PAUSE] Aguardando 30 segundos antes do próximo ativo...", level="info")
            await asyncio.sleep(30)

        emit_log(f"[ORQUESTRADOR] ✅ Ciclo de manutenção concluído — {len(eventos_ativos)} ativos processados", level="info")

        return {
            "status": "OK",
            "output": f"Processados {len(eventos_ativos)} ativos",
            "eventos": eventos_ativos
        }

    except Exception as e:
        emit_log(f"[ORQUESTRADOR] ❌ Erro: {str(e)}", level="error")
        raise HTTPException(status_code=500, detail=str(e))