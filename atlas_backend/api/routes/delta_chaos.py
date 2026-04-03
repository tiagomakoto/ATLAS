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

        await run_orbit(ticker=ticker, anos=list(range(2002, 2027)))
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
    Gerente de Integridade de Dados - v2.5.2
    Ciclo de manutenção ativo: verifica e atualiza ORBIT e REFLECT
    independentemente do status de BLOQUEIO do ativo.
    """
    from atlas_backend.core.terminal_stream import emit_log

    emit_log("[ORQUESTRADOR] 🚀 Iniciando ciclo de manutenção...", level="info")

    try:
        from atlas_backend.core.dc_runner import run_orbit, run_reflect, run_eod_preview
        from atlas_backend.core.delta_chaos_reader import get_ativo

        ativos = list_ativos()
        if not ativos:
            emit_log("[ORQUESTRADOR] Nenhum ativo parametrizado encontrado", level="warning")
            return {"status": "OK", "output": "Nenhum ativo para processar", "manutencao": []}

        xlsx_dir = _resolver_xlsx_dir(None)
        emit_log(f"[ORQUESTRADOR] Verificando {len(ativos)} ativos...", level="info")

        manutencao_realizada = []
        itens_digest = []

        for ticker in ativos:
            emit_log(f"[ORQUESTRADOR] Verificando {ticker}...", level="info")

            try:
                data = get_ativo(ticker)
            except Exception:
                emit_log(f"[ORQUESTRADOR] ⚠ {ticker} não encontrado, pulando", level="warning")
                continue

            precisa_orbit = True
            precisa_reflect = True

            if data.get("historico") and len(data.get("historico", [])) > 0:
                ultimo_ciclo = data["historico"][-1]
                data_ciclo = ultimo_ciclo.get("data_ref") or ultimo_ciclo.get("timestamp", "")[:10]
                if data_ciclo:
                    from datetime import datetime, timedelta
                    try:
                        dt_ciclo = datetime.strptime(data_ciclo, "%Y-%m-%d")
                        hoje = datetime.now()
                        dias_diff = (hoje - dt_ciclo).days
                        if dias_diff <= 35:
                            precisa_orbit = False
                    except:
                        pass

            if data.get("reflect_historico") and len(data.get("reflect_historico", [])) > 0:
                ultimo_reflect = data["reflect_historico"][-1]
                data_reflect = ultimo_reflect.get("data_ref") or ultimo_reflect.get("timestamp", "")[:10]
                if data_reflect:
                    from datetime import datetime
                    try:
                        dt_reflect = datetime.strptime(data_reflect, "%Y-%m-%d")
                        hoje = datetime.now()
                        dias_diff = (hoje - dt_reflect).days
                        if dias_diff <= 2:
                            precisa_reflect = False
                    except:
                        pass

            atualizou = False
            if precisa_orbit:
                emit_log(f"[MANUTENÇÃO] Atualizando ORBIT para {ticker} (dados desatualizados)", level="info")
                result_orbit = await run_orbit(ticker=ticker, anos=list(range(2002, 2027)))
                atualizou = True
                manutencao_realizada.append(f"ORBIT {ticker}")
                itens_digest.append({"modulo": "ORBIT", "tipo": "ok", "mensagem": f"{ticker} atualizado"})
            else:
                itens_digest.append({"modulo": "ORBIT", "tipo": "ok", "mensagem": f"{ticker} OK"})

            if precisa_reflect:
                emit_log(f"[MANUTENÇÃO] Atualizando REFLECT para {ticker} (dados desatualizados)", level="info")
                result_reflect = await run_reflect(ticker=ticker)
                atualizou = True
                manutencao_realizada.append(f"REFLECT {ticker}")
                itens_digest.append({"modulo": "REFLECT", "tipo": "ok", "mensagem": f"{ticker} atualizado"})
            else:
                itens_digest.append({"modulo": "REFLECT", "tipo": "ok", "mensagem": f"{ticker} OK"})

            if atualizou:
                emit_log(f"[MANUTENÇÃO] ✅ {ticker} atualizado", level="info")

        emit_log(f"[ORQUESTRADOR] ✅ Ciclo de manutenção concluído - {len(manutencao_realizada)} atualizações", level="info")

        return {
            "status": "OK",
            "output": f"Manutenção concluída: {manutencao_realizada}",
            "manutencao": manutencao_realizada,
            "digest": itens_digest
        }

    except Exception as e:
        emit_log(f"[ORQUESTRADOR] ❌ Erro: {str(e)}", level="error")
        raise HTTPException(status_code=500, detail=str(e))