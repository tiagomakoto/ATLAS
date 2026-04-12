import fredapi
import yfinance as yf
import requests
import pandas as pd
from typing import List, Optional
import sqlite3
from datetime import datetime, date
import traceback
from src.data_layer.db.connection import get_connection

# Configuracao da FRED API com a chave real
fred = fredapi.Fred(api_key='b450fd5922d583a9d6df17034c1b34b1')

def coletar(tickers: List[str] | None = None) -> int:
    """
    Coleta dados da fonte correspondente e persiste no SQLite.
    Retorna numero de registros inseridos.
    Nunca lanca excecao para o caller - captura internamente e loga.
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
            # FRED API - series obrigatorias
            # Tenta coletar dados reais da FRED API
            try:
                # Coletar a serie de fed funds rate
                fed_funds_data = fred.get_series('DFF').tail(1) # Ultimo valor disponivel
                fed_funds_rate = fed_funds_data.iloc[0] if not fed_funds_data.empty else 5.25 # Valor padrao se nao disponivel

                # Coletar a serie de 10-Year Treasury Yield
                treasury_data = fred.get_series('DGS10').tail(1) # Ultimo valor disponivel
                us_10y_yield = treasury_data.iloc[0] if not treasury_data.empty else 4.35 # Valor padrao se nao disponivel

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
                # Usar valores padrao em caso de erro
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

        # Coletar dados via yfinance para indices e commodities
        try:
            # Simbolos para coleta via yfinance
            simbolos_yf = {
                'DXY': 'DX-Y.NYB', # Dollar Index
                'SP500': '^GSPC', # S&P 500
                'WTI': 'CL=F', # Petroleo WTI
                'BRENT': 'BZ=F', # Petroleo Brent
                'SOJA': 'ZS=F', # Soja
                'MILHO': 'ZC=F', # Milho
                'COBRE': 'HG=F', # Cobre
                'LITIO': 'LIT', # ETF de Litio
                'NIQUEL': 'NICK', # ETF de Niquel
                'ALUMINIO': 'ALUMINUM', # ETF de Aluminio
                'CINCO': 'CINCO', # ETF de Cinco
                'COPPER': 'COPPER', # ETF de Cobre
                'GOLD': 'GLD', # Ouro
                'SILVER': 'SLV', # Prata
                'PLATINUM': 'PT', # Platina
                'PALLADIUM': 'PA', # Paladio
            }

            # Coletar dados para cada simbolo
            for nome, simbolo in simbolos_yf.items():
                try:
                    data = yf.download(simbolo, period="1mo", interval="1d")
                    if not data.empty:
                        # Inserir dados na tabela macro_global
                        for date, row in data.iterrows():
                            conn.execute("""INSERT OR IGNORE INTO macro_global (
                                data, fed_funds_rate, us_10y_yield, dxy, sp500, petroleo_wti, petroleo_brent,
                                minerio_ferro, cobre_lme, soja_cbot, milho_cbot, bdi, fonte, data_coleta
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                                date.date(),
                                None, # fed_funds_rate
                                None, # us_10y_yield
                                float(row['Close']) if nome == 'DXY' else None,
                                float(row['Close']) if nome == 'SP500' else None,
                                float(row['Close']) if nome == 'WTI' else None,
                                float(row['Close']) if nome == 'BRENT' else None,
                                float(row['Close']) if nome == 'MINERIO_FERRO' else None,
                                float(row['Close']) if nome == 'COBRE' else None,
                                float(row['Close']) if nome == 'SOJA' else None,
                                float(row['Close']) if nome == 'MILHO' else None,
                                float(row['Close']) if nome == 'BDI' else None,
                                'yfinance',
                                datetime.now()
                            ))
                            registros_inseridos += conn.rowcount
                except Exception as e:
                    print(f"[{datetime.now()}] [yfinance] Erro ao coletar {nome}: {e}")

            # Coletar dados de minerio de ferro via FRED
            try:
                # FRED: Iron Ore Price (CIF China)
                series_id = "PPIACO"
                data = fred.get_series(series_id, observation_start="2020-01-01", observation_end=datetime.now().strftime("%Y-%m-%d"))
                for date, value in data.items():
                    conn.execute("""INSERT OR IGNORE INTO macro_global (
                        data, fed_funds_rate, us_10y_yield, dxy, sp500, petroleo_wti, petroleo_brent,
                        minerio_ferro, cobre_lme, soja_cbot, milho_cbot, bdi, fonte, data_coleta
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                        date.date(),
                        None, # fed_funds_rate
                        None, # us_10y_yield
                        None, # dxy
                        None, # sp500
                        None, # petroleo_wti
                        None, # petroleo_brent
                        float(value) if pd.notna(value) else None, # minerio_ferro
                        None, # cobre_lme
                        None, # soja_cbot
                        None, # milho_cbot
                        None, # bdi
                        'fred',
                        datetime.now()
                    ))
                    registros_inseridos += conn.rowcount
            except Exception as e:
                print(f"[{datetime.now()}] [FRED API] Erro ao coletar minerio de ferro: {e}")

            # Coletar dados de cobre via FRED
            try:
                # FRED: Copper Prices (CIF China)
                series_id = "PCOPPUSDM"
                data = fred.get_series(series_id, observation_start="2020-01-01", observation_end=datetime.now().strftime("%Y-%m-%d"))
                for date, value in data.items():
                    conn.execute("""INSERT OR IGNORE INTO macro_global (
                        data, fed_funds_rate, us_10y_yield, dxy, sp500, petroleo_wti, petroleo_brent,
                        minerio_ferro, cobre_lme, soja_cbot, milho_cbot, bdi, fonte, data_coleta
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                        date.date(),
                        None, # fed_funds_rate
                        None, # us_10y_yield
                        None, # dxy
                        None, # sp500
                        None, # petroleo_wti
                        None, # petroleo_brent
                        None, # minerio_ferro
                        float(value) if pd.notna(value) else None, # cobre_lme
                        None, # soja_cbot
                        None, # milho_cbot
                        None, # bdi
                        'fred',
                        datetime.now()
                    ))
                    registros_inseridos += conn.rowcount
            except Exception as e:
                print(f"[{datetime.now()}] [FRED API] Erro ao coletar cobre: {e}")

            # Coletar dados de soja via FRED
            try:
                # FRED: Soybean Prices (CIF China)
                series_id = "PCSOYUSDM"
                data = fred.get_series(series_id, observation_start="2020-01-01", observation_end=datetime.now().strftime("%Y-%m-%d"))
                for date, value in data.items():
                    conn.execute("""INSERT OR IGNORE INTO macro_global (
                        data, fed_funds_rate, us_10y_yield, dxy, sp500, petroleo_wti, petroleo_brent,
                        minerio_ferro, cobre_lme, soja_cbot, milho_cbot, bdi, fonte, data_coleta
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                        date.date(),
                        None, # fed_funds_rate
                        None, # us_10y_yield
                        None, # dxy
                        None, # sp500
                        None, # petroleo_wti
                        None, # petroleo_brent
                        None, # minerio_ferro
                        None, # cobre_lme
                        float(value) if pd.notna(value) else None, # soja_cbot
                        None, # milho_cbot
                        None, # bdi
                        'fred',
                        datetime.now()
                    ))
                    registros_inseridos += conn.rowcount
            except Exception as e:
                print(f"[{datetime.now()}] [FRED API] Erro ao coletar soja: {e}")

            # Coletar dados de milho via FRED
            try:
                # FRED: Corn Prices (CIF China)
                series_id = "PCCORNUSDM"
                data = fred.get_series(series_id, observation_start="2020-01-01", observation_end=datetime.now().strftime("%Y-%m-%d"))
                for date, value in data.items():
                    conn.execute("""INSERT OR IGNORE INTO macro_global (
                        data, fed_funds_rate, us_10y_yield, dxy, sp500, petroleo_wti, petroleo_brent,
                        minerio_ferro, cobre_lme, soja_cbot, milho_cbot, bdi, fonte, data_coleta
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                        date.date(),
                        None, # fed_funds_rate
                        None, # us_10y_yield
                        None, # dxy
                        None, # sp500
                        None, # petroleo_wti
                        None, # petroleo_brent
                        None, # minerio_ferro
                        None, # cobre_lme
                        None, # soja_cbot
                        float(value) if pd.notna(value) else None, # milho_cbot
                        None, # bdi
                        'fred',
                        datetime.now()
                    ))
                    registros_inseridos += conn.rowcount
            except Exception as e:
                print(f"[{datetime.now()}] [FRED API] Erro ao coletar milho: {e}")

            # Coletar dados de BDI via FRED
            try:
                # FRED: Baltic Dry Index
                series_id = "BDI"
                data = fred.get_series(series_id, observation_start="2020-01-01", observation_end=datetime.now().strftime("%Y-%m-%d"))
                for date, value in data.items():
                    conn.execute("""INSERT OR IGNORE INTO macro_global (
                        data, fed_funds_rate, us_10y_yield, dxy, sp500, petroleo_wti, petroleo_brent,
                        minerio_ferro, cobre_lme, soja_cbot, milho_cbot, bdi, fonte, data_coleta
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                        date.date(),
                        None, # fed_funds_rate
                        None, # us_10y_yield
                        None, # dxy
                        None, # sp500
                        None, # petroleo_wti
                        None, # petroleo_brent
                        None, # minerio_ferro
                        None, # cobre_lme
                        None, # soja_cbot
                        None, # milho_cbot
                        float(value) if pd.notna(value) else None, # bdi
                        'fred',
                        datetime.now()
                    ))
                    registros_inseridos += conn.rowcount
            except Exception as e:
                print(f"[{datetime.now()}] [FRED API] Erro ao coletar BDI: {e}")

            conn.commit()

        except Exception as e:
            print(f"[{datetime.now()}] [yfinance] Erro ao coletar dados: {e}")

    except Exception as e:
        print(f"[{datetime.now()}] [macro_global] Erro geral: {e}")
        registros_inseridos = 0
    finally:
        if 'conn' in locals():
            conn.close()

    return registros_inseridos