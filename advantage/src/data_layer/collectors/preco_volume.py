import yfinance as yf
import requests
import pandas as pd
from typing import List, Optional
from requests.exceptions import RequestException
import sqlite3
from datetime import datetime
import traceback
from ...db.connection import get_connection

def coletar(tickers: List[str] | None = None) -> int:
    """
    Coleta dados da fonte correspondente e persiste no SQLite.
    Retorna número de registros inseridos.
    Nunca lança exceção para o caller — captura internamente e loga.
    Append-only: nunca faz UPDATE em registros existentes.
    Usa INSERT OR IGNORE para evitar duplicatas.
    """
    # Se não foi passada uma lista de tickers, usar uma lista padrão de tickers do Ibovespa
    if tickers is None:
        # Lista de tickers do Ibovespa
        tickers = ['VALE3', 'PETR4', 'BBDC4', 'ITUB4', 'PETR3', 'ABEV3', 'WEGE3', 'EMBR3', 'ENBR3', 
                  'CSNA3', 'GOAU4', 'NTCO3', 'GGBR4', 'RENT3', 'ELET3', 'LAME4', 'LREN3', 'CIEL3', 
                  'BRAP4', 'CYRE3', 'KLBN11', 'GOLL4', 'HAPV3', 'PRIO3', 'USIM5', 'BBAS3', 'RADL3', 
                  'RAIL3', 'SBSP3', 'REDE3', 'RDSA3', 'BPAC11', 'SANB11', 'SUZB3', 'CSNA3']
    
    # Contador de registros inseridos
    registros_inseridos = 0
    
    try:
        # Conectar ao banco de dados
        conn = get_connection("preco_volume")
        
        # Coletar dados para cada ticker
        for ticker in tickers:
            try:
                # Coletar dados do yfinance
                data = yf.download(ticker + ".SA", period="1mo", interval="1d")
                
                # Se não houve dados do yfinance, tentar brapi
                if data.empty:
                    # Tentar brapi como fallback
                    try:
                        # Coletar dados do brapi
                        url = f"https://api.brapi.dev/api/quote/{ticker}"
                        response = requests.get(url)
                        if response.status_code == 200:
                            dados = response.json()
                            # Processar dados do brapi
                            # (implementação futura)
                    except RequestException as e:
                        print(f"[{datetime.now()}] [brapi] Erro ao coletar dados: {e}")
                        continue
                else:
                    # Processar dados do yfinance
                    for index, row in data.iterrows():
                        try:
                            conn.execute("""
                                INSERT OR IGNORE INTO preco_volume 
                                (ticker, data, abertura, maxima, minima, fechamento, 
                                fechamento_adj, volume, fonte, data_coleta, flag_qualidade)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                ticker,
                                index.strftime('%Y-%m-%d'),
                                row[("Open", )] if ("Open", ) in row else None,
                                row[("High", )] if ("High", ) in row else None,
                                row[("Low", )] if ("Low", ) in row else None,
                                row[("Close", )] if ("Close", ) in row else None,
                                row[("Adj Close", )] if ("Adj Close", ) in row else None,
                                row[("Volume", )] if ("Volume", ) in row else None,
                                "yfinance",
                                datetime.now(),
                                1
                            ))
                            registros_inseridos += conn.rowcount
                        except Exception as e:
                            print(f"[{datetime.now()}] [preco_volume] Erro ao inserir dados: {e}")
                            continue
                            
            except Exception as e:
                print(f"[{datetime.now()}] [yfinance] Erro ao coletar dados: {e}")
                continue
                
        conn.commit()
        
    except Exception as e:
        print(f"[{datetime.now()}] [preco_volume] Erro geral: {e}")
        registros_inseridos = 0
        
    finally:
        if 'conn' in locals():
            conn.close()
            
    return registros_inseridos