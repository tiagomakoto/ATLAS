import feedparser
import json
import sqlite3
from datetime import datetime
from typing import List, Optional
import requests
import os
from src.data_layer.db.connection import get_connection

# Tentar importar o novo pacote Google GenAI
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print(f"[{datetime.now()}] [noticias] Pacote google.genai não disponível. Classificação de notícias desativada.")

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
        
        # Configurar Gemini se disponível
        cliente_gemini = None
        if GENAI_AVAILABLE:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                try:
                    cliente_gemini = genai.Client(api_key=api_key)
                except Exception as e:
                    print(f"[{datetime.now()}] [noticias] Erro ao configurar Gemini: {e}")
            else:
                print(f"[{datetime.now()}] [noticias] GEMINI_API_KEY não definida. Classificação desativada.")
        
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
                        # Classificar manchete com Gemini (se disponível)
                        score = None
                        if cliente_gemini:
                            try:
                                # Prompt para classificação de sentimento
                                prompt = f"Classifique o sentimento desta manchete em uma escala de -1.0 a +1.0, onde -1.0 é muito negativo, 0 é neutro e +1.0 é muito positivo. Responda apenas com o número decimal. Manchete: {entry.title}"
                                
                                response = cliente_gemini.models.generate_content(
                                    model="gemini-1.5-flash",
                                    contents=[prompt]
                                )
                                
                                # Extrair score da resposta
                                texto_resposta = response.text.strip()
                                score = float(texto_resposta)
                                # Garimir que está no intervalo [-1.0, 1.0]
                                score = max(-1.0, min(1.0, score))
                            except Exception as e:
                                print(f"[{datetime.now()}] [noticias] Erro ao classificar manchete: {e}")
                                score = None
                        
                        # Inserir dados no banco
                        cursor = conn.execute("""
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
                            "gemini-1.5-flash" if cliente_gemini else "none"
                        ))
                        registros_inseridos += cursor.rowcount
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