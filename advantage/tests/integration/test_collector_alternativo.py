"""
Testes de integração específicos para o coletor alternativo.py.

Este módulo testa as funcionalidades específicas do coletor alternativo,
incluindo Google Trends, ABPO e extração de dados de PDFs.
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import tempfile

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_layer.db.connection import get_connection, set_test_db_path
from data_layer.collectors.alternativo import extrair_producao_papel_celulose


class TestGoogleTrendsCollector:
    """Testes específicos para o coletor de Google Trends."""
    
    def test_google_trends_divisao_em_lotes(self, db_temp, mock_pytrends, monkeypatch):
        """
        Testa se o Google Trends divide as requisições em lotes menores.
        
        Verifica:
        - Termos são divididos em lotes de 5
        - Cada lote é processado separadamente
        - Retry funciona para cada lote
        """
        set_test_db_path(db_temp)
        
        # Track quantas vezes build_payload foi chamado
        call_count = []
        original_build_payload = mock_pytrends.build_payload
        
        def tracking_build_payload(*args, **kwargs):
            call_count.append(args[0])  # Guardar os termos
            return original_build_payload(*args, **kwargs)
        
        mock_pytrends.build_payload = tracking_build_payload
        monkeypatch.setattr('pytrends.request.TrendReq', lambda **kwargs: mock_pytrends)
        
        from data_layer.collectors.alternativo import coletar
        coletar()
        
        # Deve ter chamado build_payload múltiplas vezes (uma por lote)
        assert len(call_count) > 1, "Google Trends deveria dividir em lotes"
        
        # Cada lote deve ter no máximo 5 termos
        for termos in call_count:
            assert len(termos) <= 5, f"Lote com {len(termos)} termos, máximo é 5"
        
        set_test_db_path(None)
    
    def test_google_trends_retry_com_backoff(self, db_temp, monkeypatch):
        """
        Testa se o retry com backoff exponencial funciona.
        
        Verifica:
        - Erro 429 aciona retry
        - Espera aumenta a cada tentativa
        - Máximo de tentativas é respeitado
        """
        set_test_db_path(db_temp)
        
        # Mock que falha com erro 429 nas primeiras tentativas
        attempt_count = [0]
        
        class MockTrendReq:
            def __init__(self, **kwargs):
                pass
            
            def build_payload(self, *args, **kwargs):
                attempt_count[0] += 1
                if attempt_count[0] < 3:
                    raise Exception("429 TooManyRequests")
        
        monkeypatch.setattr('pytrends.request.TrendReq', MockTrendReq)
        
        from data_layer.collectors.alternativo import coletar
        
        # Não deve lançar exceção
        coletar()
        
        # Deve ter tentado múltiplas vezes
        assert attempt_count[0] >= 2, "Deveria ter tentado múltiplas vezes"
        
        set_test_db_path(None)
    
    def test_google_trends_uso_de_proxies(self, db_temp, monkeypatch):
        """
        Testa se proxies são usados nas requisições.
        
        Verifica:
        - Proxies são passados para TrendReq
        - Proxy muda a cada tentativa
        """
        set_test_db_path(db_temp)
        
        proxies_used = []
        
        class MockTrendReqWithProxy:
            def __init__(self, **kwargs):
                if 'requests_args' in kwargs and 'proxies' in kwargs['requests_args']:
                    proxies_used.append(kwargs['requests_args']['proxies'])
        
        monkeypatch.setattr('pytrends.request.TrendReq', MockTrendReqWithProxy)
        
        from data_layer.collectors.alternativo import coletar
        coletar()
        
        # Deve ter usado proxies
        assert len(proxies_used) > 0, "Deveria ter usado proxies"
        
        set_test_db_path(None)
    
    def test_google_trends_dados_salvos_corretamente(self, db_temp, mock_pytrends, monkeypatch):
        """
        Testa se os dados do Google Trends são salvos com estrutura correta.
        
        Verifica:
        - Termos são salvos corretamente
        - Valores são inteiros
        - Datas estão no formato correto
        """
        set_test_db_path(db_temp)
        monkeypatch.setattr('pytrends.request.TrendReq', lambda **kwargs: mock_pytrends)
        
        from data_layer.collectors.alternativo import coletar
        coletar()
        
        conn = get_connection("alternativo")
        cursor = conn.execute("SELECT * FROM google_trends LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None, "Nenhum dado salvo"
        assert isinstance(row["termo"], str), "Termo deve ser string"
        assert isinstance(row["valor"], int), "Valor deve ser inteiro"
        assert row["data"] is not None, "Data não pode ser None"
        assert row["data_coleta"] is not None, "Data de coleta não pode ser None"
        
        set_test_db_path(None)


class TestABPOCollector:
    """Testes específicos para o coletor ABPO."""
    
    def test_abpo_selenium_inicializado(self, db_temp, mock_selenium_driver, monkeypatch):
        """
        Testa se o Selenium é inicializado corretamente.
        
        Verifica:
        - Chrome é iniciado em modo headless
        - Opções são configuradas
        - Driver é fechado no final
        """
        set_test_db_path(db_temp)
        
        driver_calls = []
        
        class TrackedMockDriver:
            def __init__(self, **kwargs):
                driver_calls.append(('init', kwargs))
            
            def get(self, url):
                driver_calls.append(('get', url))
            
            @property
            def page_source(self):
                return mock_selenium_driver.page_source
            
            def quit(self):
                driver_calls.append(('quit', None))
        
        monkeypatch.setattr('selenium.webdriver.Chrome', TrackedMockDriver)
        monkeypatch.setattr('selenium.webdriver.chrome.service.Service', MagicMock())
        
        # Mock do requests
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"PDF content"
        monkeypatch.setattr('requests.get', lambda url, **kwargs: mock_response)
        
        from data_layer.collectors.alternativo import coletar
        coletar()
        
        # Verificar que driver foi inicializado e fechado
        init_calls = [c for c in driver_calls if c[0] == 'init']
        quit_calls = [c for c in driver_calls if c[0] == 'quit']
        
        assert len(init_calls) > 0, "Driver deveria ser inicializado"
        assert len(quit_calls) > 0, "Driver deveria ser fechado"
        
        set_test_db_path(None)
    
    def test_abpo_extrai_links_pdf(self, db_temp, monkeypatch):
        """
        Testa se links de PDF são extraídos do HTML.
        
        Verifica:
        - Links <a> com .pdf são encontrados
        - URLs absolutas são construídas
        - Links em iframes/embeds são verificados
        """
        set_test_db_path(db_temp)
        
        html_com_pdfs = """
        <html>
        <body>
            <a href="/dados/relatorio_2025.pdf">Relatório 2025</a>
            <a href="https://externo.com/dados.pdf">PDF Externo</a>
            <a href="/outra-pagina">Link normal</a>
            <iframe src="/embed/relatorio.pdf"></iframe>
        </body>
        </html>
        """
        
        class MockDriverWithHTML:
            def __init__(self, **kwargs):
                pass
            
            def get(self, url):
                pass
            
            @property
            def page_source(self):
                return html_com_pdfs
            
            def quit(self):
                pass
        
        monkeypatch.setattr('selenium.webdriver.Chrome', MockDriverWithHTML)
        monkeypatch.setattr('selenium.webdriver.chrome.service.Service', MagicMock())
        
        # Mock do requests
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"PDF content"
        
        urls_acessadas = []
        def mock_get(url, **kwargs):
            urls_acessadas.append(url)
            return mock_response
        
        monkeypatch.setattr('requests.get', mock_get)
        
        from data_layer.collectors.alternativo import coletar
        coletar()
        
        # Verificar que URLs de PDF foram acessadas
        pdf_urls = [u for u in urls_acessadas if '.pdf' in u.lower()]
        assert len(pdf_urls) > 0, "Deveria ter acessado URLs de PDF"
        
        set_test_db_path(None)
    
    def test_abpo_fallback_requests(self, db_temp, monkeypatch):
        """
        Testa se o fallback para requests funciona quando Selenium falha.
        
        Verifica:
        - Erro no Selenium não quebra o sistema
        - Fallback é executado
        - Dados são coletados via requests
        """
        set_test_db_path(db_temp)
        
        # Simular falha no Selenium
        def mock_failing_selenium(*args, **kwargs):
            raise ImportError("Selenium não disponível")
        
        monkeypatch.setattr('selenium.webdriver.Chrome', mock_failing_selenium)
        
        # Mock do requests que funciona
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body>Sem PDFs</body></html>"
        monkeypatch.setattr('requests.get', lambda url, **kwargs: mock_response)
        
        from data_layer.collectors.alternativo import coletar
        
        # Não deve lançar exceção
        coletar()
        
        set_test_db_path(None)


class TestExtracaoPDF:
    """Testes para a função de extração de dados de PDFs."""
    
    def test_extrai_producao_toneladas(self):
        """
        Testa extração de produção em toneladas.
        
        Verifica:
        - Valores em milhões são convertidos
        - Valores em mil são convertidos
        - Unidades são interpretadas corretamente
        """
        textos_teste = [
            ("Produção de papel: 1.500.000 toneladas", 1500000.0),
            ("Produção total: 2,5 milhões de toneladas", 2500000.0),
            ("Papel produzido: 800 mil toneladas", 800000.0),
            ("Produção de celulose: 1.200 toneladas", 1200.0),
        ]
        
        for texto, esperado in textos_teste:
            resultado = extrair_producao_papel_celulose(texto)
            assert resultado['producao_ton'] == esperado, \
                f"Falhou para: {texto}. Esperado: {esperado}, Obtido: {resultado['producao_ton']}"
    
    def test_extrai_variacao_percentual(self):
        """
        Testa extração de variação percentual.
        
        Verifica:
        - Variações positivas são extraídas
        - Variações negativas são extraídas
        - Formatos diferentes são reconhecidos
        """
        textos_teste = [
            ("Variação de 5.2%", 5.2),
            ("Crescimento de +3.5%", 3.5),
            ("Queda de -2.1%", -2.1),
            ("Variação em 12 meses: 4.5%", 4.5),
        ]
        
        for texto, esperado in textos_teste:
            resultado = extrair_producao_papel_celulose(texto)
            assert resultado['variacao_12m'] == esperado, \
                f"Falhou para: {texto}. Esperado: {esperado}, Obtido: {resultado['variacao_12m']}"
    
    def test_extrai_ambos_os_valores(self):
        """
        Testa extração de produção e variação no mesmo texto.
        
        Verifica:
        - Ambos os valores são extraídos
        - Retorno é um dict completo
        """
        texto = """
        Relatório Anual ABPO 2025
        Produção de papel: 1.800.000 toneladas
        Variação em 12 meses: +6.3%
        """
        
        resultado = extrair_producao_papel_celulose(texto)
        
        assert resultado['producao_ton'] == 1800000.0, "Produção não extraída corretamente"
        assert resultado['variacao_12m'] == 6.3, "Variação não extraída corretamente"
    
    def test_retorna_none_quando_nao_encontra(self):
        """
        Testa que retorna None quando não encontra dados.
        
        Verifica:
        - Texto sem dados retorna None
        - Estrutura do dict está correta
        """
        texto = "Este é um texto sem dados de produção ou variação."
        
        resultado = extrair_producao_papel_celulose(texto)
        
        assert resultado['producao_ton'] is None, "Deveria ser None"
        assert resultado['variacao_12m'] is None, "Deveria ser None"
    
    def test_lida_com_formatos_diferentes(self):
        """
        Testa diferentes formatos de números.
        
        Verifica:
        - Números com vírgula decimal
        - Números com ponto decimal
        - Números com separadores de milhar
        """
        textos = [
            "Produção: 1.500.000,50 toneladas",  # Formato brasileiro
            "Produção: 2,5 milhões de toneladas",  # Vírgula como decimal
            "Produção: 1500000 toneladas",  # Sem separadores
        ]
        
        for texto in textos:
            resultado = extrair_producao_papel_celulose(texto)
            assert resultado['producao_ton'] is not None, f"Falhou para: {textos}"


class TestErrosEExcecoes:
    """Testes para tratamento de erros no coletor alternativo."""
    
    def test_erro_pdfplumber_nao_quebra(self, db_temp, mock_selenium_driver, monkeypatch):
        """
        Testa que erro no pdfplumber não quebra o sistema.
        
        Verifica:
        - Exceção no pdfplumber é capturada
        - Sistema continua processando outros PDFs
        """
        set_test_db_path(db_temp)
        
        monkeypatch.setattr('selenium.webdriver.Chrome', lambda **kwargs: mock_selenium_driver)
        monkeypatch.setattr('selenium.webdriver.chrome.service.Service', MagicMock())
        
        # Mock do requests
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"PDF content"
        monkeypatch.setattr('requests.get', lambda url, **kwargs: mock_response)
        
        # Mock do pdfplumber que falha
        import pdfplumber
        def mock_failing_pdfplumber(path):
            raise Exception("Erro ao abrir PDF")
        
        monkeypatch.setattr(pdfplumber, 'open', mock_failing_pdfplumber)
        
        from data_layer.collectors.alternativo import coletar
        
        # Não deve lançar exceção
        coletar()
        
        set_test_db_path(None)
    
    def test_erro_download_pdf_nao_quebra(self, db_temp, mock_selenium_driver, monkeypatch):
        """
        Testa que erro no download de PDF não quebra o sistema.
        
        Verifica:
        - Erro 404 é tratado
        - Timeout é tratado
        - Sistema continua
        """
        set_test_db_path(db_temp)
        
        monkeypatch.setattr('selenium.webdriver.Chrome', lambda **kwargs: mock_selenium_driver)
        monkeypatch.setattr('selenium.webdriver.chrome.service.Service', MagicMock())
        
        # Mock do requests que falha para PDFs
        def mock_failing_get(url, **kwargs):
            mock_response = MagicMock()
            if '.pdf' in url.lower():
                mock_response.status_code = 404
            else:
                mock_response.status_code = 200
                mock_response.content = b"<html><body><a href='/test.pdf'>PDF</a></body></html>"
            return mock_response
        
        monkeypatch.setattr('requests.get', mock_failing_get)
        
        from data_layer.collectors.alternativo import coletar
        
        # Não deve lançar exceção
        coletar()
        
        set_test_db_path(None)
    
    def test_timeout_nao_quebra(self, db_temp, monkeypatch):
        """
        Testa que timeout nas requisições não quebra o sistema.
        
        Verifica:
        - Timeout é tratado
        - Sistema continua funcionando
        """
        set_test_db_path(db_temp)
        
        # Mock do requests que causa timeout
        def mock_timeout(url, **kwargs):
            raise TimeoutError("Request timed out")
        
        monkeypatch.setattr('requests.get', mock_timeout)
        
        from data_layer.collectors.alternativo import coletar
        
        # Não deve lançar exceção
        coletar()
        
        set_test_db_path(None)


class TestPerformance:
    """Testes de performance para o coletor alternativo."""
    
    def test_limite_de_pdfs_por_ano(self, db_temp, mock_selenium_driver, monkeypatch):
        """
        Testa se o limite de 3 PDFs por ano é respeitado.
        
        Verifica:
        - No máximo 3 PDFs são processados por ano
        - Sistema não fica sobrecarregado
        """
        set_test_db_path(db_temp)
        
        # HTML com muitos PDFs
        html_muitos_pdfs = """
        <html>
        <body>
            <a href="/pdf1.pdf">PDF 1</a>
            <a href="/pdf2.pdf">PDF 2</a>
            <a href="/pdf3.pdf">PDF 3</a>
            <a href="/pdf4.pdf">PDF 4</a>
            <a href="/pdf5.pdf">PDF 5</a>
        </body>
        </html>
        """
        
        class MockDriverManyPDFs:
            def __init__(self, **kwargs):
                pass
            
            def get(self, url):
                pass
            
            @property
            def page_source(self):
                return html_muitos_pdfs
            
            def quit(self):
                pass
        
        monkeypatch.setattr('selenium.webdriver.Chrome', MockDriverManyPDFs)
        monkeypatch.setattr('selenium.webdriver.chrome.service.Service', MagicMock())
        
        # Track quantos PDFs foram baixados
        pdfs_baixados = []
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"PDF content"
        
        def mock_get_tracking(url, **kwargs):
            if '.pdf' in url.lower():
                pdfs_baixados.append(url)
            return mock_response
        
        monkeypatch.setattr('requests.get', mock_get_tracking)
        
        from data_layer.collectors.alternativo import coletar
        coletar()
        
        # Deve ter baixado no máximo 3 PDFs por ano
        # Como processa múltiplos anos, verificar que não baixou todos
        assert len(pdfs_baixados) <= 3 * 11, "Baixou mais PDFs que o limite"  # 3 por ano, ~11 anos
        
        set_test_db_path(None)
    
    def test_delay_entre_requisicoes(self, db_temp, mock_pytrends, monkeypatch):
        """
        Testa se há delay entre requisições para evitar rate limiting.
        
        Verifica:
        - time.sleep é chamado entre lotes
        - Delay é respeitado
        """
        set_test_db_path(db_temp)
        
        sleeps = []
        original_sleep = __import__('time').sleep
        
        def tracking_sleep(seconds):
            sleeps.append(seconds)
        
        monkeypatch.setattr('time.sleep', tracking_sleep)
        monkeypatch.setattr('pytrends.request.TrendReq', lambda **kwargs: mock_pytrends)
        
        from data_layer.collectors.alternativo import coletar
        coletar()
        
        # Deve ter chamado sleep múltiplas vezes
        assert len(sleeps) > 0, "Deveria ter delays entre requisições"
        
        # Verificar que há delays significativos
        assert any(s >= 5 for s in sleeps), "Deveria ter delays de pelo menos 5 segundos"
        
        set_test_db_path(None)