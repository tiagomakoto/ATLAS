# atlas_backend/api/routes/ativos.py
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from core.paths import get_paths
from core.delta_chaos_reader import list_ativos, get_ativo, get_book, update_ativo
from core.analytics_engine import compute_walk_forward, compute_distribution, compute_acf, compute_tail_metrics
from core.schema_validator import ATLASEditableFields
from core.cache import analytics_cache
from core.book_manager import get_book_greeks, get_cobertura_seguro, get_risco_consolidado, validar_limites_risco
import pandas as pd
from pathlib import Path

router = APIRouter(prefix="/ativos", tags=["ativos"])

@router.get("", response_model=Dict[str, List[str]])
def listar_ativos():
    try:
        ativos = list_ativos()
        return {"ativos": ativos}
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="paths.json ausente")

@router.get("/book", response_model=Dict[str, Any])
def obter_book(fonte: str = Query(..., description="backtest | paper | live")):
    if fonte not in ("backtest", "paper", "live"):
        raise HTTPException(
            status_code=400,
            detail=f"fonte inválida: {fonte}. Aceitos: backtest | paper | live"
        )
    try:
        book = get_book(fonte=fonte)
        return book
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# NOVO ENDPOINT — Fase 3 (v2.3)
# =============================================================================
@router.get("/book/greeks", response_model=Dict[str, Any])
def obter_greeks_book(fonte: str = Query("paper", description="backtest | paper | live")):
    """
    Retorna greeks consolidados de todas as posições abertas.
    
    - **delta_total**: soma dos deltas
    - **gamma_total**: soma dos gammas
    - **theta_total**: soma dos thetas
    - **vega_total**: soma dos vegas
    - **delta_liquido**: delta ajustado por hedge
    - **exposicao_bruta**: soma dos valores absolutos
    - **cobertura_pct**: % short vol coberta por PUT ITM
    """
    if fonte not in ("backtest", "paper", "live"):
        raise HTTPException(
            status_code=400,
            detail=f"fonte inválida: {fonte}. Aceitos: backtest | paper | live"
        )
    
    try:
        risco = get_risco_consolidado(fonte)
        return {
            "fonte": fonte,
            "greeks": risco["greeks"],
            "cobertura": risco["cobertura"],
            "concentracao_por_ativo": risco["concentracao_por_ativo"],
            "exposicao_por_vencimento": risco["exposicao_por_vencimento"],
            "pnl_total": risco["pnl_total"],
            "total_posicoes": risco["total_posicoes"]
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/book/cobertura", response_model=Dict[str, Any])
def obter_cobertura_seguro(fonte: str = Query("paper", description="backtest | paper | live")):
    """
    Retorna % da exposição short vol coberta por PUT ITM long vol.
    Regra: P&L do seguro NUNCA consolidado com operacional.
    """
    if fonte not in ("backtest", "paper", "live"):
        raise HTTPException(
            status_code=400,
            detail=f"fonte inválida: {fonte}. Aceitos: backtest | paper | live"
        )
    
    try:
        cobertura = get_cobertura_seguro(fonte)
        return cobertura
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/book/risco", response_model=Dict[str, Any])
def obter_risco_consolidado(fonte: str = Query("paper", description="backtest | paper | live")):
    """
    Retorna visão completa de risco do book com validação de limites.
    """
    if fonte not in ("backtest", "paper", "live"):
        raise HTTPException(
            status_code=400,
            detail=f"fonte inválida: {fonte}. Aceitos: backtest | paper | live"
        )
    
    try:
        risco = get_risco_consolidado(fonte)
        validacao = validar_limites_risco(fonte)
        
        return {
            **risco,
            "validacao": {
                "dentro_limites": validacao["dentro_limites"],
                "violacoes": validacao["violacoes"],
                "alertas": validacao["alertas"]
            }
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINTS EXISTENTES
# =============================================================================
@router.get("/{ticker}", response_model=Dict[str, Any])
def obter_ativo(ticker: str):
    try:
        return get_ativo(ticker)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    except FileNotFoundError as e:
        if "paths.json" in str(e):
            raise HTTPException(status_code=503, detail="paths.json ausente")
        raise

@router.get("/{ticker}/analytics", response_model=Dict[str, Any])
async def obter_analytics(ticker: str):
    cache_key = f"analytics:{ticker}"
    cached = await analytics_cache.get(cache_key)
    if cached:
        return cached
    
    try:
        paths = get_paths()
        ativo_data = get_ativo(ticker)
        
        # Extrair ciclo_ids do historico
        ciclo_ids = [c.get("ciclo_id") for c in ativo_data.get("historico", [])]

        # Calcular IR series
        ir_series = [c.get("ir", 0) for c in ativo_data.get("historico", [])]
        
        # ✅ B02: Passar ciclo_ids para compute_walk_forward
        walk_forward = compute_walk_forward(ir_series, ciclo_ids=ciclo_ids) if ir_series else {"series": []}
        
        ohlcv_path = Path(paths["ohlcv_dir"]) / f"{ticker}.parquet"
        ohlcv_disponivel = ohlcv_path.exists()
        
        dist_stats = {}
        acf_stats = {}
        tail_stats = {}
        
        if ohlcv_disponivel:
            try:
                df = pd.read_parquet(ohlcv_path)
                if "close" in df.columns:
                    returns = (df["close"].pct_change().dropna()).tolist()
                    if len(returns) > 10:
                        dist_stats = compute_distribution(returns)
                        acf_stats = compute_acf(returns)
                        tail_stats = compute_tail_metrics(returns)
                        # ✅ CORREÇÃO: Manter TODOS os campos (incluindo p1, p99)
                        tail_stats = {
                            "skew": tail_stats.get("skew") or tail_stats.get("skewness"),
                            "kurtosis": tail_stats.get("kurtosis") or tail_stats.get("kurt"),
                            "p1": tail_stats.get("p1") or tail_stats.get("percentile_1"),  # ✅
                            "p99": tail_stats.get("p99") or tail_stats.get("percentile_99")  # ✅
                        }
                    else:
                        tail_stats = {"skew": None, "kurtosis": None, "p1": None, "p99": None}  # ✅
            except Exception:
                ohlcv_disponivel = False
                tail_stats = {"skew": None, "kurtosis": None, "p1": None, "p99": None}  # ✅
        
        result = {
            "ticker": ticker,
            "ohlcv_disponivel": ohlcv_disponivel,
            "walk_forward": walk_forward,
            "distribution": dist_stats,
            "acf": acf_stats,
            "fat_tails": tail_stats
        }
        
        await analytics_cache.set(cache_key, result)
        return result
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    except FileNotFoundError as e:
        if "paths.json" in str(e):
            raise HTTPException(status_code=503, detail="paths.json ausente")
        raise

@router.post("/{ticker}/update", response_model=Dict[str, Any])
def atualizar_ativo(ticker: str, payload: Dict[str, Any]):
    try:
        validated = ATLASEditableFields(**payload.get("data", {}))
        description = payload.get("description", "").strip()
        confirm = payload.get("confirm", False)
        
        if not description:
            raise HTTPException(status_code=400, detail="DESCRIPTION_REQUIRED")
        if not confirm:
            raise HTTPException(status_code=400, detail="CONFIRMATION_REQUIRED")
        
        result = update_ativo(ticker, validated.model_dump(), description)
        import asyncio
        asyncio.create_task(analytics_cache.clear())
        
        return result
        
    except PermissionError:
        raise HTTPException(status_code=423, detail="Ciclo ativo — lock presente")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    except Exception as e:
        if "paths.json" in str(e):
            raise HTTPException(status_code=503, detail="paths.json ausente")
        raise HTTPException(status_code=400, detail=str(e))

# =============================================================================
# NOVO ENDPOINT — Vol Premium (Fase 3)
# =============================================================================
@router.get("/{ticker}/vol-premium", response_model=Dict[str, Any])
def obter_vol_premium(ticker: str):
    """
    Retorna série histórica: IV_realizada - vol_realizada.
    Fase 3 — Item 5.3
    """
    try:
        paths = get_paths()
        ativo_data = get_ativo(ticker)
        
        historico = ativo_data.get("historico", [])
        
        vol_premium_series = []
        for ciclo in historico:
            iv_realizada = ciclo.get("iv_realizada")
            vol_realizada = ciclo.get("vol_realizada")
            
            if iv_realizada is not None and vol_realizada is not None:
                premium = iv_realizada - vol_realizada
                vol_premium_series.append({
                    "ciclo_id": ciclo.get("ciclo_id"),
                    "timestamp": ciclo.get("timestamp"),
                    "iv_realizada": iv_realizada,
                    "vol_realizada": vol_realizada,
                    "premium": round(premium, 4)
                })
        
        return {
            "ticker": ticker,
            "vol_premium": vol_premium_series,
            "total_ciclos": len(vol_premium_series)
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))