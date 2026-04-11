"""
Configuração de fixtures para testes de integração do Data Layer ADVANTAGE.

Este arquivo contém fixtures que configuram o ambiente de teste,
incluindo banco de dados temporário e mocks para serviços externos.
"""

import pytest
import tempfile
import os
import sqlite3
from datetime import datetime
from unittest.mock import MagicMock, patch


@pytest.fixture(scope="function")
def db_temp():
    """
    Fixture que cria um banco de dados SQLite temporário para testes.
    
    Retorna:
        str: Caminho do arquivo do banco de dados temporário
    
    O banco é criado em um arquivo temporário e removido automaticamente
    após o teste, garantindo isolamento entre testes.
    """
    # Criar arquivo temporário
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Criar tabelas necessárias
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabela google_trends
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS google_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            termo TEXT NOT NULL,
            data DATE NOT NULL,
            valor INTEGER,
            data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(termo, data)
        )
    """)
    
    # Tabela abpo_papelao
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS abpo_papelao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data DATE NOT NULL,
            producao_ton REAL,
            variacao_12m REAL,
            fonte_url TEXT,
            data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(data)
        )
    """)
    
    # Tabela temperatura_noticias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS temperatura_noticias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            data DATE NOT NULL,
            hora_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            score REAL,
            volume_noticias INTEGER DEFAULT 1,
            manchetes_raw TEXT,
            modelo TEXT,
            UNIQUE(ticker, data, hora_coleta)
        )
    """)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Limpar após o teste
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture(scope="function")
def mock_pytrends():
    """
    Fixture que fornece um mock para o TrendReq do pytrends.
    
    Retorna:
        MagicMock: Mock configurado para simular respostas do Google Trends
    """
    mock = MagicMock()
    
    # Simular dados de interesse ao longo do tempo
    import pandas as pd
    from datetime import datetime, timedelta
    
    # Criar DataFrame simulado
    dates = pd.date_range(start='2025-03-01', end='2025-04-01', freq='D')
    data = {
        'Vale': [50 + i % 20 for i in range(len(dates))],
        'Petrobras': [60 + i % 15 for i in range(len(dates))],
        'isPartial': [False] * len(dates)
    }
    mock_df = pd.DataFrame(data, index=dates)
    
    mock.interest_over_time.return_value = mock_df
    
    return mock


@pytest.fixture(scope="function")
def mock_gemini_client():
    """
    Fixture que fornece um mock para o cliente Gemini.
    
    Retorna:
        MagicMock: Mock configurado para simular respostas da API Gemini
    """
    mock = MagicMock()
    
    # Simular resposta de classificação de sentimento
    mock_response = MagicMock()
    mock_response.text = "0.75"
    
    mock.models.generate_content.return_value = mock_response
    
    return mock


@pytest.fixture(scope="function")
def mock_selenium_driver():
    """
    Fixture que fornece um mock para o WebDriver do Selenium.
    
    Retorna:
        MagicMock: Mock configurado para simular o comportamento do Selenium
    """
    mock = MagicMock()
    
    # Simular HTML com links de PDF
    mock.page_source = """
    <html>
    <body>
        <a href="/dados/relatorio_2025.pdf">Relatório 2025</a>
        <a href="/dados/relatorio_2024.pdf">Relatório 2024</a>
    </body>
    </html>
    """
    
    return mock


@pytest.fixture(scope="function")
def mock_pdf_response():
    """
    Fixture que fornece um mock para resposta de download de PDF.
    
    Retorna:
        MagicMock: Mock configurado para simular download de PDF
    """
    mock = MagicMock()
    mock.status_code = 200
    
    # Conteúdo simulado de PDF (não é um PDF real, apenas para testes)
    mock.content = b"PDF content simulation"
    
    return mock


@pytest.fixture(scope="function")
def env_test(monkeypatch):
    """
    Fixture que configura variáveis de ambiente para testes.
    
    Define variáveis necessárias para execução dos testes sem
    expor credenciais reais.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "test_api_key_12345")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("COLLECTION_INTERVAL", "60")


@pytest.fixture(scope="function")
def mock_feedparser():
    """
    Fixture que fornece um mock para o feedparser.
    
    Retorna:
        MagicMock: Mock configurado para simular feeds RSS
    """
    mock = MagicMock()
    
    # Simular entradas de feed
    entry1 = MagicMock()
    entry1.title = "Mercado financeiro em alta hoje"
    
    entry2 = MagicMock()
    entry2.title = "Inflação cai no Brasil"
    
    mock.entries = [entry1, entry2]
    
    return mock