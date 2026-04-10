import feedparser
import google.generativeai as genai
import json
import sqlite3
from datetime import datetime
from typing import List, Optional
import requests
from ...db.connection import get_connection

# Configuração do modelo Gemini (substitua 'sua-api-key' pela chave real)
# genai.configure(api_key='sua-api-key')

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
        conn = get_connection("alternativo")
        
        # Coletar dados de notícias via RSS
        feeds = [
            "https://www.infomoney.com.br/feed/",
            "https://www.valor.com.br/rss/brasil",
        ]
        
        # Processar cada feed
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                # Processar as entradas do feed
                for entry in feed.entries:
                    try:
                        # Classificar manchete com Gemini (simulado)
                        score = 0.0  # Valor padrão, será substituído pela classificação real
                        
                        # Inserir dados no banco
                        conn.execute("""
                            INSERT OR IGNORE INTO temperatura_noticias 
                            (ticker, data, hora_coleta, score, volume_noticias, manchetes_raw, modelo)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            None,  # ticker (NULL = mercado geral)
                            datetime.now().date(),
                            datetime.now(),
                            score,
                            1,  # volume_noticias
                            json.dumps([entry.title]),  # manchetes_raw
                            "gemini-2.5-flash"  # modelo
                        ))
                        registros_inseridos += conn.rowcount
                    except Exception as e:
                        print(f"[{datetime.now()}] [noticias] Erro ao processar entrada: {e}")
                        continue
                        
            except Exception as e:
                print(f"[{datetime.now()}] [noticias] Erro ao coletar feed {feed_url}: {e}")
                continue
        
        conn.commit()
        
    except Exception as e:
        print(f"[{datetime.now()}] [noticias] Erro geral: {e}")
        registros_inseridos = 0
        
    finally:
        if 'conn' in locals():
            conn.close()
            
    return registros_inseridos