#════════════════════════════════════════════════════════════════════
#DELTA CHAOS — atlas_backend/api/routes/delta_chaos.py
#Endpoints FastAPI — Seção 6 do prompt de migração
#WS REMOVIDO: Centralizado em main.py (/ws/logs)
#════════════════════════════════════════════════════════════════════
import sys
import os
_parent = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _parent not in sys.path:
    sys.path.insert(0, _parent)

import json
import asyncio
from datetime import date
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from atlas_backend.core.terminal_stream import emit_log, emit_error

router = APIRouter(prefix="/delta-chaos", tags=["delta-chaos"])

#── Modelos de request ───────────────────────────────────────────────
class EodExecutarPayload(BaseModel):
    xlsx_dir:    Optional[str] = None
    confirm:     bool          = False
    description: str           = ""

class OrbitPayload(BaseModel):
    ticker:      str
    confirm:     bool = False
    description: str  = ""

class TunePayload(BaseModel):
    ticker:      str
    confirm:     bool = False
    description: str  = ""

class GatePayload(BaseModel):
    ticker:      str
    confirm:     bool = False
    description: str  = ""

#── Validação de arquivo EOD (Seção 8) ──────────────────────────────
def validar_eod(filepath: str) -> dict:
    try:
        df = pd.read_excel(filepath, header=1)
    except Exception as e:
        return {"valido": False, "motivo": f"Arquivo ilegível: {e}"}
    if len(df) < 5:
        return {"valido": False, "motivo": f"Arquivo com {len(df)} linhas — suspeito"}
    colunas = [str(c).lower().strip() for c in df.columns]
    if not any("strike" in c for c in colunas):
        return {"valido": False, "motivo": "Coluna 'strike' não encontrada"}
    pct_nan = df.isnull().mean().mean()
    if pct_nan > 0.80:
        return {"valido": False, "motivo": f"Arquivo com {pct_nan:.0%} de valores ausentes"}
    return {"valido": True}

#── Helpers ──────────────────────────────────────────────────────────
def _require_confirm(confirm: bool, endpoint: str) -> None:
    if not confirm:
        raise HTTPException(status_code=400, detail=f"{endpoint}: confirm=false.")

def _lazy_edge(universo: list, capital: int = 10_000, modo: str = "paper"):
    from delta_chaos.edge import EDGE
    return EDGE(capital=capital, modo=modo, universo=universo)

def _lazy_gate_eod(ticker: str, verbose: bool = True) -> str:
    from delta_chaos.gate_eod import gate_eod
    return gate_eod(ticker, verbose=verbose)

def _lazy_executar_gate(ticker: str) -> str:
    from delta_chaos.gate import executar_gate
    return executar_gate(ticker)

def _lazy_executar_tune(ticker: str) -> dict:
    from delta_chaos.tune import executar_tune
    return executar_tune(ticker)

def _universo_configurado() -> list:
    import os
    from delta_chaos.init import ATIVOS_DIR
    if not os.path.exists(ATIVOS_DIR):
        return []
    return [f.replace(".json", "").upper() for f in os.listdir(ATIVOS_DIR) if f.endswith(".json")]

#── [1/2] EOD Preview ───────────────────────────────────────────────
@router.post("/eod/preview")
async def eod_preview():
    ativos = _universo_configurado()
    if not ativos:
        raise HTTPException(status_code=404, detail="Nenhum ativo configurado em ATIVOS_DIR.")
    aprovados = []
    excluidos = []
    for ativo in ativos:
        try:
            parecer = _lazy_gate_eod(ativo, verbose=False)
        except Exception as e:
            parecer = "BLOQUEADO"
            emit_error(e)
        entry = {"ticker": ativo, "parecer": parecer}
        if parecer in ("BLOQUEADO", "GATE VENCIDO"):
            excluidos.append(entry)
        else:
            aprovados.append(entry)
    emit_log(f"EOD preview — {len(aprovados)} aprovados, {len(excluidos)} excluídos")
    return {"data": str(date.today()), "aprovados": aprovados, "excluidos": excluidos, "instrucao": "Revise e confirme em /eod/executar"}

#── [2/2] EOD Executar ───────────────────────────────────────────────
@router.post("/eod/executar")
async def eod_executar(payload: EodExecutarPayload):
    _require_confirm(payload.confirm, "EOD executar")
    from delta_chaos.init import OPCOES_HOJE_DIR
    xlsx_dir = payload.xlsx_dir or OPCOES_HOJE_DIR
    import os
    ativos = _universo_configurado()
    for ativo in ativos:
        xlsx_path = os.path.join(xlsx_dir, f"{ativo}.xlsx")
        if os.path.exists(xlsx_path):
            resultado_val = validar_eod(xlsx_path)
            if not resultado_val["valido"]:
                raise HTTPException(status_code=422, detail={"ativo": ativo, "motivo": resultado_val["motivo"]})
    emit_log(f"EOD iniciado — {payload.description or str(date.today())}")
    resultado_df = None
    erro = None
    try:
        edge = _lazy_edge(universo=ativos, modo="paper")
        resultado_df = edge.executar_eod(xlsx_dir=xlsx_dir)
        emit_log(f"EOD processado — {len(resultado_df) if resultado_df is not None else 0} registros")
    except Exception as e:
        erro = str(e)
        emit_error(e)
    if erro:
        raise HTTPException(status_code=500, detail=f"EOD falhou: {erro}")
    n_linhas = len(resultado_df) if resultado_df is not None else 0
    emit_log(f"EOD concluído — {n_linhas} registros no BOOK")
    return {"status": "ok", "data": str(date.today()), "description": payload.description, "book_linhas": n_linhas}

#── ORBIT ─────────────────────────────────────────────────────────────
@router.post("/orbit")
async def orbit_endpoint(payload: OrbitPayload):
    _require_confirm(payload.confirm, "ORBIT")
    emit_log(f"ORBIT iniciado — {payload.ticker} ({payload.description or 'sem descrição'})")
    erro = None
    resultado = None
    try:
        from delta_chaos.tape import tape_backtest, tape_carregar_ativo
        from delta_chaos.orbit import ORBIT as _ORBIT
        import datetime as _dt
        ticker = payload.ticker.strip().upper()
        cfg = tape_carregar_ativo(ticker)
        anos = cfg.get("anos_validos", list(range(2018, _dt.date.today().year + 1)))
        anos_orbit = list(range(min(anos) - 2, _dt.date.today().year + 1))
        df_tape = tape_backtest(ativos=[ticker], anos=anos_orbit, forcar=False)
        if df_tape.empty:
            raise ValueError(f"TAPE vazio para {ticker}")
        orbit = _ORBIT(universo={ticker: cfg})
        df_regimes = orbit.rodar(df_tape, anos_orbit, modo="mensal")
        resultado = {"ticker": ticker, "ciclos": len(df_regimes) if not df_regimes.empty else 0, "ultimo_ciclo": str(df_regimes["ciclo_id"].max()) if not df_regimes.empty else "N/A"}
    except Exception as e:
        erro = str(e)
        emit_error(e)
    if erro:
        raise HTTPException(status_code=500, detail=f"ORBIT falhou: {erro}")
    emit_log(f"ORBIT concluído — {resultado['ciclos']} ciclos, último: {resultado['ultimo_ciclo']}")
    return {"status": "ok", **resultado}

#── TUNE ──────────────────────────────────────────────────────────────
@router.post("/tune")
async def tune_endpoint(payload: TunePayload):
    _require_confirm(payload.confirm, "TUNE")
    emit_log(f"TUNE iniciado — {payload.ticker} ({payload.description or 'sem descrição'})")
    resultado = None
    erro = None
    try:
        resultado = _lazy_executar_tune(payload.ticker)
    except Exception as e:
        erro = str(e)
        emit_error(e)
    if erro:
        raise HTTPException(status_code=500, detail=f"TUNE falhou: {erro}")
    melhor = resultado["melhor_ir_valido"]
    emit_log(f"TUNE concluído — melhor: {melhor['label']} TP={melhor['tp']} STOP={melhor['stop']} IR={melhor['ir_valido']:+.3f}")
    return {"status": "ok", "ticker": resultado["ticker"], "aviso": "Resultado registrado. NÃO aplicado — requer confirmação do CEO.", "melhor_ir_valido": resultado["melhor_ir_valido"], "melhor_pnl_valido": resultado["melhor_pnl_valido"], "todas_combinacoes": resultado["resultados"]}

#── GATE ──────────────────────────────────────────────────────────────
@router.post("/gate")
async def gate_endpoint(payload: GatePayload):
    ticker = payload.ticker.strip().upper()
    
    print(f"[GATE DEBUG] >>> INÍCIO: {ticker}")
    emit_log(f"[GATE] >>> INÍCIO: {ticker}", level="debug")
    await asyncio.sleep(0)  # ← FORÇA EVENT LOOP PROCESSAR TASKS
    
    _require_confirm(payload.confirm, "GATE")

    emit_log(f"GATE iniciado — {ticker} ({payload.description or 'sem descrição'})")
    await asyncio.sleep(0)  # ← FORÇA EVENT LOOP PROCESSAR TASKS
    print(f"[GATE DEBUG] emit_log() chamado para 'GATE iniciado'")

    resultado_str = None
    erro = None
    
    try:
        print(f"[GATE DEBUG] Chamando _lazy_executar_gate({ticker})...")
        resultado_str = _lazy_executar_gate(ticker)
        print(f"[GATE DEBUG] _lazy_executar_gate retornou: {resultado_str}")
        
    except ValueError as e:
        print(f"[GATE DEBUG] ValueError capturado: {e}")
        emit_log(f"GATE bloqueado: {e}", level="warning")
        await asyncio.sleep(0)  # ← FORÇA EVENT LOOP PROCESSAR TASKS
        emit_log(f"[GATE] <<< FIM: {ticker} | resultado=EXCLUÍDO", level="debug")
        await asyncio.sleep(0)  # ← FORÇA EVENT LOOP PROCESSAR TASKS
        print(f"[GATE DEBUG] <<< FIM: EXCLUÍDO")
        return {"resultado": "EXCLUÍDO", "detalhes": {"motivo": str(e)}}
        
    except Exception as e:
        print(f"[GATE DEBUG] Exception genérica: {type(e).__name__}: {e}")
        erro = str(e)
        emit_error(e)
        await asyncio.sleep(0)  # ← FORÇA EVENT LOOP PROCESSAR TASKS

    if erro:
        print(f"[GATE DEBUG] Lançando HTTPException: {erro}")
        emit_log(f"[GATE] <<< FIM: {ticker} | resultado=ERRO", level="debug")
        await asyncio.sleep(0)  # ← FORÇA EVENT LOOP PROCESSAR TASKS
        raise HTTPException(status_code=500, detail=f"GATE falhou: {erro}")

    print(f"[GATE DEBUG] Emitindo log de conclusão...")
    emit_log(f"GATE concluído — {ticker}: {resultado_str}")
    await asyncio.sleep(0)  # ← FORÇA EVENT LOOP PROCESSAR TASKS
    print(f"[GATE DEBUG] emit_log() chamado para 'GATE concluído'")
    
    emit_log(f"[GATE] <<< FIM: {ticker} | resultado={resultado_str}", level="debug")
    await asyncio.sleep(0)  # ← FORÇA EVENT LOOP PROCESSAR TASKS
    print(f"[GATE DEBUG] <<< FIM: {resultado_str}")

    return {
        "resultado": resultado_str,
        "ticker": ticker,
        "detalhes": {"description": payload.description},
    }