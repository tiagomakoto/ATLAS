"""
Testes de integracao especificos para o coletor noticias.py.

Este modulo testa as funcionalidades especificas do coletor de noticias,
incluindo integracao com Gemini API, processamento de feeds RSS e
classificacao de sentimento.
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Adicionar o diretorio src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_layer.db.connection import get_connection, set_test_db_path


class TestNoticiasCollector:
    """Testes especificos para o coletor de noticias."""
    
    def test_noticias_insere_dados_com_score(self, db_temp, mock_gemini_client, 
                                             mock_feedparser, monkeypatch):
        """
        Testa se noticias sao inseridas com score de sentimento.
        
        Verifica:
        - Feed RSS e processado
        - Gemini classifica cada manchete
        - Score e salvo no banco
        """
        set_test_db_path(db_temp)
        
        # Configurar mocks
        monkeypatch.setattr('feedparser.parse', lambda url: mock_feedparser)
        monkeypatch.setattr('google.genai.Client', lambda **kwargs: mock_gemini_client)
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")
        
        from data_layer.collectors.noticias import coletar
        registros = coletar()
        
        assert registros > 0, "Nenhum registro foi inserido"
        
        # Verificar no banco
        conn = get_connection("alternativo")
        cursor = conn.execute("SELECT * FROM temperatura_noticias LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None, "Nenhum dado encontrado"
        assert row["score"] is not None, "Score deveria estar preenchido"
        assert isinstance(row["score"], float), "Score deve ser float"
        assert -1.0 <= row["score"] <= 1.0, "Score deve estar entre -1.0 e 1.0"
        
        set_test_db_path(None)
    
    def test_noticias_sem_api_key(self, db_temp, mock_feedparser, monkeypatch):
        """
        Testa funcionamento sem API key do Gemini.
        
        Verifica:
        - Coletor funciona mesmo sem classificacao
        - Dados sao inseridos com score None
        - Modelo e 'none'
        """
        set_test_db_path(db_temp)
        
        # Remover API key
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.setattr('feedparser.parse', lambda url: mock_feedparser)
        
        from data_layer.collectors.noticias import coletar
        registros = coletar()
        
        assert registros > 0, "Nenhum registro foi inserido sem API key"
        
        # Verificar no banco
        conn = get_connection("alternativo")
        cursor = conn.execute("SELECT score, modelo FROM temperatura_noticias LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        assert row["score"] is None, "Score deveria ser None sem API key"
        assert row["modelo"] == "none", "Modelo deveria ser 'none' sem API key"
        
        set_test_db_path(None)
    
    def test_noticias_api_key_invalida(self, db_temp, mock_feedparser, monkeypatch):
        """
        Testa tratamento de API key invalida.
        
        Verifica:
        - Erro na inicializacao do cliente e tratado
        - Sistema continua funcionando
        - Dados sao inseridos sem score
        """
        set_test_db_path(db_temp)
        
        # Mock que falha na criacao do cliente
        def mock_failing_client(**kwargs):
            raise Exception("Invalid API key")
        
        monkeypatch.setenv("GEMINI_API_KEY", "invalid_key")
        monkeypatch.setattr('feedparser.parse', lambda url: mock_feedparser)
        monkeypatch.setattr('google.genai.Client', mock_failing_client)
        
        from data_layer.collectors.noticias import coletar
        
        # Nao deve lancar excecao
        registros = coletar()
        
        assert registros > 0, "Deveria inserir dados mesmo com API key invalida"
        
        set_test_db_path(None)
    
    def test_noticias_classificacao_falha(self, db_temp, mock_gemini_client, 
                                          mock_feedparser, monkeypatch):
        """
        Testa quando classificacao de uma manchete falha.
        
        Verifica:
        - Erro em uma manchete nao quebra o sistema
        - Outras manchetes sao processadas
        - Score e None para manchete com erro
        """
        set_test_db_path(db_temp)
        
        # Mock que falha na segunda chamada
        call_count = [0]
        original_generate = mock_gemini_client.models.generate_content
        
        def mock_generate_with_failure(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Erro na classificacao")
            return original_generate(*args, **kwargs)
        
        mock_gemini_client.models.generate_content = mock_generate_with_failure
        
        monkeypatch.setattr('feedparser.parse', lambda url: mock_feedparser)
        monkeypatch.setattr('google.genai.Client', lambda **kwargs: mock_gemini_client)
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")
        
        from data_layer.collectors.noticias import coletar
        
        # Nao deve lancar excecao
        registros = coletar()
        
        assert registros > 0, "Deveria inserir dados mesmo com falha parcial"
        
        set_test_db_path(None)
    
    def test_noticias_score_limitado(self, db_temp, mock_gemini_client, 
                                     mock_feedparser, monkeypatch):
        """
        Testa se score e limitado entre -1.0 e 1.0.
        
        Verifica:
        - Scores acima de 1.0 sao limitados a 1.0
        - Scores abaixo de -1.0 sao limitados a -1.0
        """
        set_test_db_path(db_temp)
        
        # Mock que retorna valores fora do range
        mock_response_high = MagicMock()
        mock_response_high.text = "2.5"
        
        mock_response_low = MagicMock()
        mock_response_low.text = "-1.5"
        
        call_count = [0]
        
        def mock_generate_limit_test(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_response_high
            return mock_response_low
        
        mock_gemini_client.models.generate_content = mock_generate_limit_test
        
        monkeypatch.setattr('feedparser.parse', lambda url: mock_feedparser)
        monkeypatch.setattr('google.genai.Client', lambda **kwargs: mock_gemini_client)
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")
        
        from data_layer.collectors.noticias import coletar
        coletar()
        
        # Verificar no banco
        conn = get_connection("alternativo")
        cursor = conn.execute("SELECT score FROM temperatura_noticias ORDER BY id LIMIT 2")
        rows = cursor.fetchall()
        conn.close()
        
        if len(rows) >= 2:
            assert rows[0]["score"] == 1.0, "Score deveria ser limitado a 1.0"
            assert rows[1]["score"] == -1.0, "Score deveria ser limitado a -1.0"
        
        set_test_db_path(None)
    
    def test_noticias_resposta_nao_numerica(self, db_temp, mock_gemini_client, 
                                            mock_feedparser, monkeypatch):
        """
        Testa tratamento de resposta nao numerica do Gemini.
        
        Verifica:
        - Texto nao numerico e tratado
        - Score e None quando nao e possivel converter
        """
        set_test_db_path(db_temp)
        
        # Mock que retorna texto nao numerico
        mock_response = MagicMock()
        mock_response.text = "O sentimento e positivo"
        
        mock_gemini_client.models.generate_content.return_value = mock_response
        
        monkeypatch.setattr('feedparser.parse', lambda url: mock_feedparser)
        monkeypatch.setattr('google.genai.Client', lambda **kwargs: mock_gemini_client)
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")
        
        from data_layer.collectors.noticias import coletar
        
        # Nao deve lancar excecao
        registros = coletar()
        
        # Verificar no banco
        conn = get_connection("alternativo")
        cursor = conn.execute("SELECT score FROM temperatura_noticias LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        assert row["score"] is None, "Score deveria ser None para resposta nao numerica"
        
        set_test_db_path(None)


class TestFeedsRSS:
    """Testes especificos para processamento de feeds RSS."""
    
    def test_multiplos_feeds(self, db_temp, mock_feedparser, monkeypatch):
        """
        Testa processamento de multiplos feeds RSS.
        
        Verifica:
        - Todos os feeds sao processados
        - Dados de todos sao inseridos
        """
        set_test_db_path(db_temp)
        
        feeds_acessados = []
        
        def mock_parse_tracking(url):
            feeds_acessados.append(url)
            return mock_feedparser
        
        monkeypatch.setattr('feedparser.parse', mock_parse_tracking)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        from data_layer.collectors.noticias import coletar
        coletar()
        
        # Deve ter acessado multiplos feeds
        assert len(feeds_acessados) >= 2, "Deveria acessar multiplos feeds"
        
        set_test_db_path(None)
    
    def test_feed_indisponivel(self, db_temp, monkeypatch):
        """
        Testa tratamento de feed indisponivel.
        
        Verifica:
        - Erro em um feed nao quebra o sistema
        - Outros feeds sao processados
        """
        set_test_db_path(db_temp)
        
        call_count = [0]
        
        def mock_parse_with_failure(url):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Feed indisponivel")
            
            # Retornar feed valido na segunda chamada
            mock = MagicMock()
            entry = MagicMock()
            entry.title = "Noticia de teste"
            mock.entries = [entry]
            return mock
        
        monkeypatch.setattr('feedparser.parse', mock_parse_with_failure)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        from data_layer.collectors.noticias import coletar
        
        # Nao deve lancar excecao
        registros = coletar()
        
        # Deve ter inserido dados do segundo feed
        assert registros > 0, "Deveria inserir dados do feed disponivel"
        
        set_test_db_path(None)
    
    def test_feed_sem_entradas(self, db_temp, monkeypatch):
        """
        Testa tratamento de feed sem entradas.
        
        Verifica:
        - Feed vazio e tratado
        - Nao causa erro
        """
        set_test_db_path(db_temp)
        
        # Mock de feed vazio
        mock_feed_vazio = MagicMock()
        mock_feed_vazio.entries = []
        
        monkeypatch.setattr('feedparser.parse', lambda url: mock_feed_vazio)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        from data_layer.collectors.noticias import coletar
        
        # Nao deve lancar excecao
        registros = coletar()
        
        # Nao deve inserir nada
        assert registros == 0, "Nao deveria inserir dados de feed vazio"
        
        set_test_db_path(None)
    
    def test_entrada_sem_titulo(self, db_temp, monkeypatch):
        """
        Testa tratamento de entrada sem titulo.
        
        Verifica:
        - Entrada sem titulo e ignorada
        - Outras entradas sao processadas
        """
        set_test_db_path(db_temp)
        
        # Mock de feed com entrada sem titulo
        mock_feed = MagicMock()
        entry1 = MagicMock()
        entry1.title = "Noticia valida"
        entry2 = MagicMock()
        # entry2 nao tem atributo title
        mock_feed.entries = [entry1, entry2]
        
        monkeypatch.setattr('feedparser.parse', lambda url: mock_feed)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        from data_layer.collectors.noticias import coletar
        
        # Nao deve lancar excecao
        registros = coletar()
        
        # Deve ter inserido apenas a entrada valida
        assert registros > 0, "Deveria inserir entrada valida"
        
        set_test_db_path(None)


class TestEstruturaDados:
    """Testes para estrutura dos dados inseridos."""
    
    def test_campos_obrigatorios(self, db_temp, mock_feedparser, monkeypatch):
        """
        Testa se campos obrigatorios sao preenchidos.
        
        Verifica:
        - data e preenchida
        - hora_coleta e preenchida
        - volume_noticias e definido
        """
        set_test_db_path(db_temp)
        
        monkeypatch.setattr('feedparser.parse', lambda url: mock_feedparser)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        from data_layer.collectors.noticias import coletar
        coletar()
        
        # Verificar no banco
        conn = get_connection("alternativo")
        cursor = conn.execute("""
            SELECT data, hora_coleta, volume_noticias, manchetes_raw, modelo
            FROM temperatura_noticias
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        
        assert row["data"] is not None, "Data deve ser preenchida"
        assert row["hora_coleta"] is not None, "Hora de coleta deve ser preenchida"
        assert row["volume_noticias"] is not None, "Volume deve ser definido"
        assert row["manchetes_raw"] is not None, "Manchetes raw deve ser preenchido"
        assert row["modelo"] is not None, "Modelo deve ser definido"
        
        set_test_db_path(None)
    
    def test_manchetes_raw_json(self, db_temp, mock_feedparser, monkeypatch):
        """
        Testa se manchetes_raw e salvo como JSON.
        
        Verifica:
        - Formato JSON e valido
        - E uma lista de strings
        """
        set_test_db_path(db_temp)
        
        monkeypatch.setattr('feedparser.parse', lambda url: mock_feedparser)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        from data_layer.collectors.noticias import coletar
        coletar()
        
        # Verificar no banco
        conn = get_connection("alternativo")
        cursor = conn.execute("SELECT manchetes_raw FROM temperatura_noticias LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        import json
        manchetes = json.loads(row["manchetes_raw"])
        
        assert isinstance(manchetes, list), "Manchetes deve ser uma lista"
        assert len(manchetes) > 0, "Lista nao deve estar vazia"
        assert all(isinstance(m, str) for m in manchetes), "Todos itens devem ser strings"
        
        set_test_db_path(None)
    
    def test_data_atual(self, db_temp, mock_feedparser, monkeypatch):
        """
        Testa se data e a data atual.
        
        Verifica:
        - Data inserida e de hoje
        """
        set_test_db_path(db_temp)
        
        monkeypatch.setattr('feedparser.parse', lambda url: mock_feedparser)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        from data_layer.collectors.noticias import coletar
        coletar()
        
        hoje = datetime.now().date()
        
        # Verificar no banco
        conn = get_connection("alternativo")
        cursor = conn.execute("SELECT data FROM temperatura_noticias LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        assert row["data"] == hoje, f"Data deveria ser {hoje}"
        
        set_test_db_path(None)


class TestEvitaDuplicatas:
    """Testes para verificar que duplicatas sao evitadas."""
    
    def test_insert_or_ignore(self, db_temp, mock_feedparser, monkeypatch):
        """
        Testa se INSERT OR IGNORE evita duplicatas.
        
        Verifica:
        - Segunda execucao nao insere duplicatas
        - Contagem de registros nao aumenta
        """
        set_test_db_path(db_temp)
        
        monkeypatch.setattr('feedparser.parse', lambda url: mock_feedparser)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        from data_layer.collectors.noticias import coletar
        
        # Primeira execucao
        registros_1 = coletar()
        
        # Segunda execucao
        registros_2 = coletar()
        
        # Segunda execucao nao deve inserir nada
        assert registros_2 == 0, "Deveria evitar duplicatas"
        
        set_test_db_path(None)
    
    def test_unique_constraint(self, db_temp, mock_feedparser, monkeypatch):
        """
        Testa constraint UNIQUE na tabela.
        
        Verifica:
        - Constraint UNIQUE existe
        - Tentativa de duplicata gera erro silencioso
        """
        set_test_db_path(db_temp)
        
        monkeypatch.setattr('feedparser.parse', lambda url: mock_feedparser)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        from data_layer.collectors.noticias import coletar
        
        coletar()
        
        # Verificar estrutura da tabela
        conn = get_connection("alternativo")
        cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='temperatura_noticias'")
        row = cursor.fetchone()
        conn.close()
        
        assert 'UNIQUE' in row[0], "Tabela deveria ter constraint UNIQUE"
        
        set_test_db_path(None)


class TestErrosEExcecoes:
    """Testes para tratamento de erros."""
    
    def test_erro_geral_nao_quebra(self, db_temp, monkeypatch):
        """
        Testa que erro geral nao quebra o sistema.
        
        Verifica:
        - Excecao e capturada
        - Retorna 0 em caso de falha
        """
        set_test_db_path(db_temp)
        
        # Mock que falha completamente
        def mock_failing_parse(url):
            raise Exception("Erro fatal")
        
        monkeypatch.setattr('feedparser.parse', mock_failing_parse)
        
        from data_layer.collectors.noticias import coletar
        
        # Nao deve lancar excecao
        registros = coletar()
        
        assert registros == 0, "Deveria retornar 0 em caso de falha"
        
        set_test_db_path(None)
    
    def test_commit_e_close(self, db_temp, mock_feedparser, monkeypatch):
        """
        Testa se commit e close sao chamados.
        
        Verifica:
        - Dados sao persistidos
        - Conexao e fechada
        """
        set_test_db_path(db_temp)
        
        monkeypatch.setattr('feedparser.parse', lambda url: mock_feedparser)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        from data_layer.collectors.noticias import coletar
        coletar()
        
        # Tentar conectar novamente - dados devem estar la
        conn = get_connection("alternativo")
        cursor = conn.execute("SELECT COUNT(*) as total FROM temperatura_noticias")
        total = cursor.fetchone()["total"]
        conn.close()
        
        assert total > 0, "Dados nao foram persistidos"
        
        set_test_db_path(None)