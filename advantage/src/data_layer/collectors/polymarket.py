"""
polymarket.py — Coletor de mercados de predição do Polymarket

Coleta dados de mercados de predição relevantes para o mercado brasileiro da API do Polymarket.
API: https://gamma-api.polymarket.com/markets
Filtros: categorias copom, fed, politica_brasil, recessao_global, commodity
Liquidez mínima: USD 10.000
Frequência: diária (adicionar ao job_diario)
"""

import requests
import json
from typing import List, Optional
import sqlite3
from datetime import datetime
from src.data_layer.db.connection import get_connection

def coletar(tickers: List[str] | None = None) -> int:
    """
    Coleta mercados de predição do Polymarket relevantes para B3.
    API: https://gamma-api.polymarket.com/markets
    Filtros: categorias copom, fed, politica_brasil, recessao_global, commodity
    Mínimo de liquidez: USD 10.000 (filtrar ruído)
    Frequência: diária (adicionar ao job_diario)
    
    Returns:
        int: número de registros inseridos
    """
    # Contador de registros inseridos
    registros_inseridos = 0
    
    try:
        # Conectar ao banco de dados
        conn = get_connection("alternativo")
        
        # URL da API do Polymarket
        url = "https://gamma-api.polymarket.com/markets"
        
        # Fazer requisição à API
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"[{datetime.now()}] [polymarket] Erro ao acessar API: {response.status_code}")
            return 0
        
        # Parse do JSON
        data = response.json()
        
        # Filtros de categorias permitidas
        categorias_permitidas = {
            "copom", 
            "fed", 
            "politica_brasil", 
            "recessao_global", 
            "commodity"
        }
        
        # Processar cada mercado
        for market in data:
            try:
                # Verificar se o mercado tem categoria válida
                categoria = market.get("category", "").lower()
                if categoria not in categorias_permitidas:
                    continue
                
                # Verificar liquidez mínima (USD 10.000)
                liquidity = market.get("liquidity", 0)
                if liquidity < 10000:
                    continue
                
                # Extrair dados do mercado
                data_market = market.get("date", "")
                timestamp = market.get("timestamp", "")
                market_id = market.get("id", "")
                descricao_evento = market.get("question", "")
                probabilidade = market.get("lastPrice", 0)
                variacao_24h = market.get("change24h", 0)
                liquidez_usd = market.get("liquidity", 0)
                
                # Tentar extrair impacto na B3 e ticker afetado
                impacto_b3 = ""
                ticker_afetado = ""
                
                # Buscar por termos relacionados a B3 e ações brasileiras
                descricao_lower = descricao_evento.lower()
                if "b3" in descricao_lower or "ibovespa" in descricao_lower or "bovespa" in descricao_lower:
                    impacto_b3 = "alto"
                elif "selic" in descricao_lower or "juros" in descricao_lower:
                    impacto_b3 = "alto"
                elif "inflação" in descricao_lower or "ipca" in descricao_lower:
                    impacto_b3 = "alto"
                elif "dólar" in descricao_lower or "usd" in descricao_lower:
                    impacto_b3 = "medio"
                
                # Tentar extrair ticker afetado
                # Buscar por padrões de tickers (4-6 letras maiúsculas)
                import re
                tickers_brasileiros = re.findall(r"[A-Z]{4,6}", descricao_evento)
                if tickers_brasileiros:
                    ticker_afetado = tickers_brasileiros[0]
                
                # Inserir no banco de dados
                conn.execute("""INSERT OR IGNORE INTO polymarket_eventos (
                    data, 
                    timestamp, 
                    market_id, 
                    descricao_evento, 
                    categoria, 
                    probabilidade, 
                    variacao_24h, 
                    liquidez_usd, 
                    impacto_b3, 
                    ticker_afetado, 
                    fonte, 
                    data_coleta
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                    data_market,
                    timestamp,
                    market_id,
                    descricao_evento,
                    categoria,
                    probabilidade,
                    variacao_24h,
                    liquidez_usd,
                    impacto_b3,
                    ticker_afetado,
                    "polymarket",
                    datetime.now()
                ))
                
                registros_inseridos += conn.rowcount
                
            except Exception as e:
                print(f"[{datetime.now()}] [polymarket] Erro ao processar mercado: {e}")
                continue
        
        conn.commit()
        
    except Exception as e:
        print(f"[{datetime.now()}] [polymarket] Erro geral: {e}")
        registros_inseridos = 0
        
    finally:
        if 'conn' in locals():
            conn.close()
    
    return registros_inseridos