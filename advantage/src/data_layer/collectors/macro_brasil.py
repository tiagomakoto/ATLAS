import requests
import pandas as pd
from typing import List, Optional
import sqlite3
from datetime import datetime
import traceback
from src.data_layer.db.connection import get_connection

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
        
        # Coletar dados do BCB/SGS
        series_bcb = {
            432: "selic_meta",
            11: "selic_efetiva",
            433: "ipca_mensal",
            13522: "ipca_acum_12m",
            189: "igpm_mensal",
            1: "cambio_usd_brl"
        }
        
        # Coletar dados para cada série do BCB
        for codigo, nome_coluna in series_bcb.items():
            try:
                url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json"
                response = requests.get(url)
                if response.status_code == 200:
                    dados = response.json()
                    # Processar dados e inserir no banco
                    for item in dados:
                        try:
                            conn.execute(f"""
                                INSERT OR IGNORE INTO macro_brasil 
                                (data, {nome_coluna}, fonte, data_coleta)
                                VALUES (?, ?, ?, ?)
                            """, (
                                item['data'],
                                item['valor'],
                                "BCB/SGS",
                                datetime.now()
                            ))
                            registros_inseridos += conn.rowcount
                        except Exception as e:
                            print(f"[{datetime.now()}] [macro_brasil] Erro ao inserir dados: {e}")
                            continue
                else:
                    print(f"[{datetime.now()}] [BCB/SGS] Erro ao coletar série {codigo}: {response.status_code}")
            except Exception as e:
                print(f"[{datetime.now()}] [BCB/SGS] Erro ao coletar série {codigo}: {e}")
                continue
        
        # Coletar dados do Focus BCB
        try:
            # Coletar expectativas de mercado anuais
            url = "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais"
            response = requests.get(url)
            if response.status_code == 200:
                dados = response.json()
                # Processar dados e inserir no banco
                for item in dados.get('value', []):
                    try:
                        conn.execute("""
                            INSERT OR IGNORE INTO focus_bcb_historico 
                            (data_referencia, indicador, horizonte, mediana, media, 
                            desvio_padrao, minimo, maximo, data_coleta)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            item.get('DataReferencia', ''),
                            item.get('Indicador', ''),
                            item.get('Horizonte', ''),
                            item.get('Mediana', None),
                            item.get('Media', None),
                            item.get('DesvioPadrao', None),
                            item.get('Minimo', None),
                            item.get('Maximo', None),
                            datetime.now()
                        ))
                        registros_inseridos += conn.rowcount
                    except Exception as e:
                        print(f"[{datetime.now()}] [focus_bcb] Erro ao inserir dados: {e}")
                        continue
            else:
                print(f"[{datetime.now()}] [Focus BCB] Erro ao coletar dados: {response.status_code}")
        except Exception as e:
            print(f"[{datetime.now()}] [Focus BCB] Erro ao coletar dados: {e}")
        
        conn.commit()
        
    except Exception as e:
        print(f"[{datetime.now()}] [macro_brasil] Erro geral: {e}")
        registros_inseridos = 0
        
    finally:
        if 'conn' in locals():
            conn.close()
            
    return registros_inseridos