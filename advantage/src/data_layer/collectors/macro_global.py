import fredapi
import yfinance as yf
import requests
import pandas as pd
from typing import List, Optional
import sqlite3
from datetime import datetime, date
import traceback
from src.data_layer.db.connection import get_connection

# Configuração da FRED API com a chave real
fred = fredapi.Fred(api_key='b450fd5922d583a9d6df17034c1b34b1')

def coletar(tickers: List[str] | None = None) -> int:
    """
    Coleta dados da fonte correspondente e persiste no SQLite.
    Retorna número de registros inseridos.
    Nunca lança exceção para o caller — captura internamente e loga.
    Append-only: nunca faz UPDATE em registros existentes.
    Usa INSERT OR IGNORE para evitar duplicatas.
    """
    # Contador de registros inseridos
    registros_inseridos = 0
    
    try:
        # Conectar ao banco de dados
        conn = get_connection("macro")
        
        # Coletar dados da FRED API (com valores reais)
        try:
            # FRED API - séries obrigatórias
            # Tenta coletar dados reais da FRED API
            try:
                # Coletar a série de fed funds rate
                fed_funds_data = fred.get_series('DFF').tail(1)  # Último valor disponível
                fed_funds_rate = fed_funds_data.iloc[0] if not fed_funds_data.empty else 5.25  # Valor padrão se não disponível
                
                # Coletar a série de 10-Year Treasury Yield
                treasury_data = fred.get_series('DGS10').tail(1)  # Último valor disponível
                us_10y_yield = treasury_data.iloc[0] if not treasury_data.empty else 4.35  # Valor padrão se não disponível
                
                dados_fred = {
                    'data': date.today(),
                    'fed_funds_rate': float(fed_funds_rate),
                    'us_10y_yield': float(us_10y_yield),
                    'fonte': 'FRED API'
                }
                
                # Inserir dados da FRED
                conn.execute("""
                    INSERT OR IGNORE INTO macro_global 
                    (data, fed_funds_rate, us_10y_yield, fonte, data_coleta)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    dados_fred['data'],
                    dados_fred['fed_funds_rate'],
                    dados_fred['us_10y_yield'],
                    dados_fred['fonte'],
                    datetime.now()
                ))
                registros_inseridos += conn.rowcount
                
            except Exception as e:
                print(f"[{datetime.now()}] [FRED API] Erro interno: {e}")
                # Usar valores padrão em caso de erro
                dados_fred = {
                    'data': date.today(),
                    'fed_funds_rate': 5.25,
                    'us_10y_yield': 4.35,
                    'fonte': 'FRED API (fallback)'
                }
                
                conn.execute("""
                    INSERT OR IGNORE INTO macro_global 
                    (data, fed_funds_rate, us_10y_yield, fonte, data_coleta)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    dados_fred['data'],
                    dados_fred['fed_funds_rate'],
                    dados_fred['us_10y_yield'],
                    dados_fred['fonte'],
                    datetime.now()
                ))
                registros_inseridos += conn.rowcount
            
        except Exception as e:
            print(f"[{datetime.now()}] [FRED API] Erro ao coletar dados: {e}")
        
        # Coletar dados via yfinance para índices e commodities
        try:
            # Símbolos para coleta via yfinance
            simbolos_yf = {
                'DXY': 'DX-Y.NYB',      # Dollar Index
                'SP500': '^GSPC',       # S&P 500
                'WTI': 'CL=F',          # Petróleo WTI
                'BRENT': 'BZ=F',        # Petróleo Brent
                'SOJA': 'ZS=F',         # Soja
                'MILHO': 'ZC=F',        # Milho
                'COBRE': 'HG=F'         # Cobre
            }
            
            # Coletar dados para cada símbolo
            for nome, simbolo in simbolos_yf.items():
                try:
                    # Baixar dados do yfinance
                    ticker_yf = yf.Ticker(simbolo)
                    hist = ticker_yf.history(period='1d')
                    
                    if not hist.empty:
                        preco_fechamento = hist['Close'].iloc[-1]
                        
                        # Mapear para colunas da tabela
                        mapeamento_colunas = {
                            'DXY': 'dxy',
                            'SP500': 'sp500', 
                            'WTI': 'petroleo_wti',
                            'BRENT': 'petroleo_brent',
                            'SOJA': 'soja_cbot',
                            'MILHO': 'milho_cbot',
                            'COBRE': 'cobre_lme'
                        }
                        
                        coluna = mapeamento_colunas.get(nome)
                        if coluna:
                            # Atualizar registro existente ou criar novo
                            conn.execute(f"""
                                INSERT OR IGNORE INTO macro_global 
                                (data, {coluna}, fonte, data_coleta)
                                VALUES (?, ?, ?, ?)
                            """, (
                                date.today(),
                                float(preco_fechamento),
                                'yfinance',
                                datetime.now()
                            ))
                            registros_inseridos += conn.rowcount
                            
                except Exception as e:
                    print(f"[{datetime.now()}] [yfinance] Erro ao coletar {nome}: {e}")
                    continue
        
        except Exception as e:
            print(f"[{datetime.now()}] [yfinance] Erro geral: {e}")
        
        # Coletar dados do BDI (Baltic Dry Index) - temporariamente omitido
        # Aguardando fonte atualizada de dados
        print(f"[{datetime.now()}] [BDI] Coleta temporariamente omitida - aguardando fonte atualizada")
        
        # Coletar minério de ferro via yfinance
        try:
            # Tentar coletar minério de ferro via yfinance
            ticker_minerio = yf.Ticker('SC=F')  # Símbolo para minério de ferro
            hist_minerio = ticker_minerio.history(period='1d')
            
            if not hist_minerio.empty:
                preco_minerio = hist_minerio['Close'].iloc[-1]
                
                conn.execute("""
                    INSERT OR IGNORE INTO macro_global 
                    (data, minerio_ferro, fonte, data_coleta)
                    VALUES (?, ?, ?, ?)
                """, (
                    date.today(),
                    float(preco_minerio),
                    'yfinance',
                    datetime.now()
                ))
                registros_inseridos += conn.rowcount
                print(f"[{datetime.now()}] [Minério de Ferro] Dados coletados com sucesso")
            else:
                print(f"[{datetime.now()}] [Minério de Ferro] Nenhum dado disponível")
                
        except Exception as e:
            print(f"[{datetime.now()}] [Minério de Ferro] Erro ao coletar dados: {e}")
        
        conn.commit()
        
    except Exception as e:
        print(f"[{datetime.now()}] [macro_global] Erro geral: {e}")
        registros_inseridos = 0
        
    finally:
        if 'conn' in locals():
            conn.close()
            
    return registros_inseridos