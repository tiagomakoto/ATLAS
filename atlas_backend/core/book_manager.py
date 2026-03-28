# atlas_backend/core/book_manager.py
"""
Gerenciamento do book de posições e agregação de greeks.
Fase 3 — ATLAS v2.3
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.paths import get_paths


def get_book_greeks(fonte: str = "paper") -> Dict[str, Any]:
    """
    Agrega greeks de todas as posições abertas.
    
    Args:
        fonte: "backtest" | "paper" | "live"
    
    Returns:
        Dicionário com greeks consolidados:
        - delta_total: soma dos deltas
        - gamma_total: soma dos gammas
        - theta_total: soma dos thetas
        - vega_total: soma dos vegas
        - delta_liquido: delta ajustado por hedge
        - exposicao_bruta: soma dos valores absolutos
        - posicoes: lista detalhada
    """
    if fonte not in ("backtest", "paper", "live"):
        raise ValueError(f"fonte inválida: {fonte}. Aceitos: backtest | paper | live")
    
    paths = get_paths()
    book_path = os.path.join(paths["book_dir"], f"book_{fonte}.json")
    
    if not os.path.exists(book_path):
        raise FileNotFoundError(f"BOOK_{fonte.upper()} não encontrado: {book_path}")
    
    with open(book_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    posicoes = data.get("ops", [])
    
    # Inicializar acumuladores
    delta_total = 0.0
    gamma_total = 0.0
    theta_total = 0.0
    vega_total = 0.0
    delta_liquido = 0.0
    exposicao_bruta = 0.0
    
    posicoes_detalhadas = []
    
    for pos in posicoes:
        core = pos.get("core", {})
        legs = pos.get("legs", [])
        greeks = pos.get("greeks", {})
        
        # Extrair greeks da posição
        delta_pos = greeks.get("delta", 0.0) or 0.0
        gamma_pos = greeks.get("gamma", 0.0) or 0.0
        theta_pos = greeks.get("theta", 0.0) or 0.0
        vega_pos = greeks.get("vega", 0.0) or 0.0
        
        # Acumular
        delta_total += delta_pos
        gamma_total += gamma_pos
        theta_total += theta_pos
        vega_total += vega_pos
        
        # Delta líquido (considerando sinal)
        delta_liquido += delta_pos
        
        # Exposição bruta (valor absoluto)
        exposicao_bruta += abs(delta_pos)
        
        # Detalhar posição
        posicoes_detalhadas.append({
            "op_id": pos.get("op_id"),
            "ativo": core.get("ativo"),
            "estrategia": core.get("estrategia"),
            "delta": delta_pos,
            "gamma": gamma_pos,
            "theta": theta_pos,
            "vega": vega_pos,
            "pnl": core.get("pnl", 0.0) or 0.0,
            "tipo": legs[0].get("tipo") if legs else None
        })
    
    return {
        "fonte": fonte,
        "delta_total": round(delta_total, 4),
        "gamma_total": round(gamma_total, 4),
        "theta_total": round(theta_total, 4),
        "vega_total": round(vega_total, 4),
        "delta_liquido": round(delta_liquido, 4),
        "exposicao_bruta": round(exposicao_bruta, 4),
        "total_posicoes": len(posicoes),
        "posicoes": posicoes_detalhadas,
        "pnl_total": sum(
            (pos.get("core", {}).get("pnl", 0.0) or 0.0)
            for pos in posicoes
        )
    }


def get_cobertura_seguro(fonte: str = "paper") -> Dict[str, Any]:
    """
    Calcula % da exposição short vol coberta por PUT ITM long vol.
    
    Returns:
        Dicionário com:
        - exposicao_short_vol: valor total
        - cobertura_put_itm: valor coberto
        - cobertura_pct: porcentagem
    """
    if fonte not in ("backtest", "paper", "live"):
        raise ValueError(f"fonte inválida: {fonte}. Aceitos: backtest | paper | live")
    
    paths = get_paths()
    book_path = os.path.join(paths["book_dir"], f"book_{fonte}.json")
    
    if not os.path.exists(book_path):
        raise FileNotFoundError(f"BOOK_{fonte.upper()} não encontrado: {book_path}")
    
    with open(book_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    posicoes = data.get("ops", [])
    
    exposicao_short_vol = 0.0
    cobertura_put_itm = 0.0
    
    for pos in posicoes:
        core = pos.get("core", {})
        legs = pos.get("legs", [])
        greeks = pos.get("greeks", {})
        
        vega_pos = greeks.get("vega", 0.0) or 0.0
        
        # Identificar short vol (vega negativo)
        if vega_pos < 0:
            exposicao_short_vol += abs(vega_pos)
        
        # Identificar PUT ITM long vol (vega positivo + tipo PUT + ITM)
        for leg in legs:
            if (vega_pos > 0 and 
                leg.get("tipo", "").upper() == "PUT" and 
                leg.get("moneyness", "") == "ITM"):
                cobertura_put_itm += vega_pos
    
    cobertura_pct = (
        (cobertura_put_itm / exposicao_short_vol * 100)
        if exposicao_short_vol > 0
        else 0.0
    )
    
    return {
        "exposicao_short_vol": round(exposicao_short_vol, 4),
        "cobertura_put_itm": round(cobertura_put_itm, 4),
        "cobertura_pct": round(cobertura_pct, 2),
        "fonte": fonte
    }


def get_risco_consolidado(fonte: str = "paper") -> Dict[str, Any]:
    """
    Retorna métricas consolidadas de risco do book.
    
    Returns:
        Dicionário completo com:
        - greeks: agregação total
        - cobertura: % de proteção
        - concentracao: risco por ativo
        - vencimentos: exposição por data
    """
    greeks = get_book_greeks(fonte)
    cobertura = get_cobertura_seguro(fonte)
    
    # Calcular concentração por ativo
    concentracao = {}
    for pos in greeks["posicoes"]:
        ativo = pos["ativo"]
        if ativo not in concentracao:
            concentracao[ativo] = {
                "delta": 0.0,
                "vega": 0.0,
                "posicoes": 0
            }
        concentracao[ativo]["delta"] += pos["delta"]
        concentracao[ativo]["vega"] += pos["vega"]
        concentracao[ativo]["posicoes"] += 1
    
    # Calcular exposição por vencimento
    vencimentos = {}
    paths = get_paths()
    book_path = os.path.join(paths["book_dir"], f"book_{fonte}.json")
    
    with open(book_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for pos in data.get("ops", []):
        legs = pos.get("legs", [])
        for leg in legs:
            venc = leg.get("vencimento")
            if venc:
                if venc not in vencimentos:
                    vencimentos[venc] = {
                        "delta": 0.0,
                        "vega": 0.0,
                        "posicoes": 0
                    }
                greeks_leg = pos.get("greeks", {})
                vencimentos[venc]["delta"] += greeks_leg.get("delta", 0.0) or 0.0
                vencimentos[venc]["vega"] += greeks_leg.get("vega", 0.0) or 0.0
                vencimentos[venc]["posicoes"] += 1
    
    return {
        "fonte": fonte,
        "greeks": {
            "delta_total": greeks["delta_total"],
            "gamma_total": greeks["gamma_total"],
            "theta_total": greeks["theta_total"],
            "vega_total": greeks["vega_total"],
            "delta_liquido": greeks["delta_liquido"],
            "exposicao_bruta": greeks["exposicao_bruta"]
        },
        "cobertura": {
            "short_vol": cobertura["exposicao_short_vol"],
            "protecao_put_itm": cobertura["cobertura_put_itm"],
            "cobertura_pct": cobertura["cobertura_pct"]
        },
        "concentracao_por_ativo": concentracao,
        "exposicao_por_vencimento": vencimentos,
        "pnl_total": greeks["pnl_total"],
        "total_posicoes": greeks["total_posicoes"]
    }


def validar_limites_risco(fonte: str = "paper", limites: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Valida se o book está dentro dos limites de risco.
    
    Args:
        fonte: "backtest" | "paper" | "live"
        limites: dicionário com limites máximos (opcional)
    
    Returns:
        Dicionário com:
        - dentro_limites: bool
        - violacoes: lista de violações
        - alertas: lista de alertas
    """
    # Limites default
    if limites is None:
        limites = {
            "delta_max": 100.0,
            "gamma_max": 5.0,
            "vega_max": 50.0,
            "theta_max": -10.0,  # negativo é OK (ganhar tempo)
            "cobertura_min_pct": 20.0
        }
    
    risco = get_risco_consolidado(fonte)
    greeks = risco["greeks"]
    cobertura = risco["cobertura"]
    
    violacoes = []
    alertas = []
    
    # Validar delta
    if abs(greeks["delta_liquido"]) > limites["delta_max"]:
        violacoes.append({
            "metrica": "delta_liquido",
            "valor": greeks["delta_liquido"],
            "limite": limites["delta_max"],
            "mensagem": f"Delta líquido {greeks['delta_liquido']:.2f} excede limite {limites['delta_max']:.2f}"
        })
    
    # Validar gamma
    if abs(greeks["gamma_total"]) > limites["gamma_max"]:
        violacoes.append({
            "metrica": "gamma_total",
            "valor": greeks["gamma_total"],
            "limite": limites["gamma_max"],
            "mensagem": f"Gamma total {greeks['gamma_total']:.4f} excede limite {limites['gamma_max']:.4f}"
        })
    
    # Validar vega
    if abs(greeks["vega_total"]) > limites["vega_max"]:
        violacoes.append({
            "metrica": "vega_total",
            "valor": greeks["vega_total"],
            "limite": limites["vega_max"],
            "mensagem": f"Vega total {greeks['vega_total']:.2f} excede limite {limites['vega_max']:.2f}"
        })
    
    # Validar cobertura
    if cobertura["cobertura_pct"] < limites["cobertura_min_pct"]:
        alertas.append({
            "metrica": "cobertura_pct",
            "valor": cobertura["cobertura_pct"],
            "limite": limites["cobertura_min_pct"],
            "mensagem": f"Cobertura {cobertura['cobertura_pct']:.1f}% abaixo do mínimo {limites['cobertura_min_pct']:.1f}%"
        })
    
    return {
        "fonte": fonte,
        "dentro_limites": len(violacoes) == 0,
        "violacoes": violacoes,
        "alertas": alertas,
        "timestamp": Path(book_path).stat().st_mtime if (book_path := os.path.join(get_paths()["book_dir"], f"book_{fonte}.json")) and os.path.exists(book_path) else None
    }