# atlas_backend/api/routes/delta_chaos.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from atlas_backend.core.dc_runner import (
    run_eod_preview, run_eod,
    run_orbit, run_tune, run_gate
)
from atlas_backend.core.delta_chaos_reader import list_ativos
from atlas_backend.core.paths import get_paths
from pathlib import Path

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

        await run_orbit(ticker=ticker, anos=list(range(2002, 2026)))
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
    Gateway para execução do ciclo completo do orquestrador.
    Inicia com EOD Preview (Check Status).
    """
    try:
        from atlas_backend.core.dc_runner import run_eod_preview
        xlsx_dir = _resolver_xlsx_dir(None)
        result = await run_eod_preview(xlsx_dir=xlsx_dir)
        return {"status": result["status"], "output": result["output"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))