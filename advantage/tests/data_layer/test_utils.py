import pytest
import pandas as pd
import sys
import os

# Adicionar o caminho do projeto ao sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_layer.utils import (
    validar_ohlcv, 
    log_coleta, 
    retry, 
    validar_data, 
    validar_ticker,
    formatar_moeda,
    calcular_variacao_percentual
)

def test_validar_ohlcv():
    """Testa a função de validação OHLCV"""
    # Dados válidos
    dados_validos = pd.DataFrame({
        'abertura': [10.0, 11.0],
        'maxima': [12.0, 13.0],
        'minima': [9.0, 10.0],
        'fechamento': [11.0, 12.0],
        'volume': [1000, 2000]
    })
    
    resultado = validar_ohlcv(dados_validos)
    assert 'flag_qualidade' in resultado.columns
    assert resultado['flag_qualidade'].sum() == 2  # Ambos válidos
    
    # Dados inválidos (abertura > máxima)
    dados_invalidos = pd.DataFrame({
        'abertura': [15.0],
        'maxima': [12.0],
        'minima': [9.0],
        'fechamento': [11.0],
        'volume': [1000]
    })
    
    resultado = validar_ohlcv(dados_invalidos)
    assert resultado['flag_qualidade'].iloc[0] == 0

def test_log_coleta():
    """Testa a função de log"""
    # Testar log sem erro
    log_coleta("test_fonte", 10)
    
    # Testar log com erro
    log_coleta("test_fonte", 0, "erro_teste")
    
    # Verificar que não lança exceção
    assert True

def test_retry_decorator():
    """Testa o decorator de retry"""
    
    @retry(tentativas=2, espera_s=0.1)
    def funcao_que_falha():
        raise ValueError("Erro simulado")
    
    # Verificar que lança exceção após todas as tentativas
    with pytest.raises(ValueError):
        funcao_que_falha()

def test_validar_data():
    """Testa a validação de datas"""
    assert validar_data("2024-01-01") == True
    assert validar_data("2024-13-01") == False  # Mês inválido
    assert validar_data("01-01-2024") == False  # Formato inválido

def test_validar_ticker():
    """Testa a validação de tickers"""
    assert validar_ticker("PETR4") == True
    assert validar_ticker("VALE3") == True
    assert validar_ticker("ABC") == False  # Muito curto
    assert validar_ticker("ABCDEFG") == False  # Muito longo

def test_formatar_moeda():
    """Testa a formatação de valores monetários"""
    assert formatar_moeda(1234.56) == "R$ 1.234,56"
    assert formatar_moeda(None) == "N/A"

def test_calcular_variacao_percentual():
    """Testa o cálculo de variação percentual"""
assert calcular_variacao_percentual(110, 100) == 10.0
assert calcular_variacao_percentual(90, 100) == -10.0
assert calcular_variacao_percentual(100, 0) == 0.0 # Divisão por zero


class TestAlterTableIfColumnMissing(unittest.TestCase):
    """Testes para a função alter_table_if_column_missing"""

    def setUp(self):
        """Configuração antes de cada teste."""
        # Criar banco de teste
        self.test_db_path = Path("/tmp/test_utils.db")
        self.test_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Criar banco de dados de teste
        self.conn = sqlite3.connect(str(self.test_db_path))
        self.conn.execute("""CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY,
            nome TEXT
        )""")
        self.conn.commit()

    def tearDown(self):
        """Limpeza após cada teste."""
        if hasattr(self, 'conn'):
            self.conn.close()
        if hasattr(self, 'test_db_path') and self.test_db_path.exists():
            self.test_db_path.unlink()

    def test_alter_table_if_column_missing_adds_column(self):
        """Verifica que a função adiciona uma coluna que não existe."""
        # Verificar que a coluna não existe inicialmente
        cursor = self.conn.execute("PRAGMA table_info(test_table)")
        colunas_existentes = [row[1] for row in cursor.fetchall()]
        self.assertNotIn('idade', colunas_existentes)
        
        # Chamar a função para adicionar a coluna
        alter_table_if_column_missing(self.conn, 'test_table', 'idade', 'INTEGER')
        
        # Verificar que a coluna foi adicionada
        cursor = self.conn.execute("PRAGMA table_info(test_table)")
        colunas_existentes = [row[1] for row in cursor.fetchall()]
        self.assertIn('idade', colunas_existentes)

    def test_alter_table_if_column_missing_idempotent(self):
        """Verifica que a função é idempotente (não adiciona coluna se já existir)."""
        # Adicionar a coluna pela primeira vez
        alter_table_if_column_missing(self.conn, 'test_table', 'idade', 'INTEGER')
        
        # Verificar que a coluna foi adicionada
        cursor = self.conn.execute("PRAGMA table_info(test_table)")
        colunas_existentes = [row[1] for row in cursor.fetchall()]
        self.assertIn('idade', colunas_existentes)
        
        # Contar o número de colunas antes da segunda chamada
        num_colunas_antes = len(colunas_existentes)
        
        # Chamar a função novamente (deve ser idempotente)
        alter_table_if_column_missing(self.conn, 'test_table', 'idade', 'INTEGER')
        
        # Verificar que o número de colunas não mudou
        cursor = self.conn.execute("PRAGMA table_info(test_table)")
        colunas_existentes = [row[1] for row in cursor.fetchall()]
        num_colunas_depois = len(colunas_existentes)
        self.assertEqual(num_colunas_antes, num_colunas_depois)
        
        # Verificar que a coluna ainda existe
        self.assertIn('idade', colunas_existentes)

    def test_alter_table_if_column_missing_different_type(self):
        """Verifica que a função não altera o tipo da coluna se já existir."""
        # Adicionar a coluna como INTEGER
        alter_table_if_column_missing(self.conn, 'test_table', 'idade', 'INTEGER')
        
        # Verificar que a coluna foi adicionada
        cursor = self.conn.execute("PRAGMA table_info(test_table)")
        colunas_existentes = [row[1] for row in cursor.fetchall()]
        self.assertIn('idade', colunas_existentes)
        
        # Tentar adicionar a mesma coluna com tipo diferente (deve ser ignorado)
        alter_table_if_column_missing(self.conn, 'test_table', 'idade', 'TEXT')
        
        # Verificar que o tipo ainda é INTEGER (não foi alterado)
        cursor = self.conn.execute("PRAGMA table_info(test_table)")
        for row in cursor.fetchall():
            if row[1] == 'idade':
                self.assertEqual(row[2], 'INTEGER')
                break
        
        # Verificar que a coluna ainda existe
        colunas_existentes = [row[1] for row in cursor.fetchall()]
        self.assertIn('idade', colunas_existentes)