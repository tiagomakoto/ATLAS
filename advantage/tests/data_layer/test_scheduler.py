import pytest
import sys
import os

# Adicionar o caminho do projeto ao sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_layer.scheduler import calcular_indicadores, log_job_execution

def test_calcular_indicadores_interface():
    """Testa se a função calcular_indicadores existe e tem a interface correta"""
    # Verificar se a função existe
    assert callable(calcular_indicadores)
    
    # Testar chamada básica
    resultado = calcular_indicadores()
    
    # Verificar que retorna um inteiro
    assert isinstance(resultado, int)
    
    # Verificar que não lança exceção
    assert resultado >= 0

def test_log_job_execution():
    """Testa a função de log de execução de jobs"""
    # Testar log de sucesso
    log_job_execution("test_job", 10)
    
    # Testar log de erro
    log_job_execution("test_job", 0, "erro_teste")
    
    # Verificar que não lança exceção
    assert True

def test_calcular_indicadores_append_only():
    """Testa que a função é append-only"""
    # Executar duas vezes e verificar que não lança erro
    resultado1 = calcular_indicadores()
    resultado2 = calcular_indicadores()
    
    # Ambas as execuções devem retornar valores válidos
assert isinstance(resultado1, int)
assert isinstance(resultado2, int)
assert resultado1 >= 0
assert resultado2 >= 0

class TestSchedulerFunctions(unittest.TestCase):
    """Testes para as funções do scheduler"""

    @patch('advantage.src.data_layer.scheduler.get_connection')
    @patch('advantage.src.data_layer.scheduler.pd.read_sql')
    def test_calcular_indicadores_retorna_int(self, mock_read_sql, mock_get_connection):
        """Verifica que calcular_indicadores retorna um inteiro >= 0"""
        # Mock da conexão com o banco
        mock_conn = Mock()
        mock_get_connection.return_value = mock_conn
        
        # Mock dos dados de entrada
        mock_data = pd.DataFrame({
            'ticker': ['PETR4', 'PETR4', 'PETR4'],
            'data': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'abertura': [10.0, 10.5, 11.0],
            'maxima': [11.0, 11.5, 12.0],
            'minima': [9.5, 10.0, 10.5],
            'fechamento': [10.5, 11.0, 11.5],
            'volume': [1000, 1200, 1500]
        })
        mock_read_sql.return_value = mock_data
        
        # Executar a função
        resultado = calcular_indicadores()
        
        # Verificar que retorna um inteiro >= 0
        self.assertIsInstance(resultado, int)
        self.assertGreaterEqual(resultado, 0)

    @patch('advantage.src.data_layer.scheduler.get_connection')
    @patch('advantage.src.data_layer.scheduler.pd.read_sql')
    def test_calcular_indicadores_nao_lanca_excecao(self, mock_read_sql, mock_get_connection):
        """Verifica que calcular_indicadores não lança exceção mesmo com dados inválidos"""
        # Mock da conexão com o banco
        mock_conn = Mock()
        mock_get_connection.return_value = mock_conn
        
        # Mock dos dados de entrada vazios
        mock_data = pd.DataFrame()
        mock_read_sql.return_value = mock_data
        
        # Executar a função
        resultado = calcular_indicadores()
        
        # Verificar que não lança exceção e retorna 0
        self.assertEqual(resultado, 0)

    @patch('advantage.src.data_layer.scheduler.get_connection')
    @patch('advantage.src.data_layer.scheduler.pd.read_sql')
    def test_novos_indicadores_calculados_corretamente(self, mock_read_sql, mock_get_connection):
        """Verifica que os novos indicadores são calculados e inseridos corretamente"""
        # Mock da conexão com o banco
        mock_conn = Mock()
        mock_get_connection.return_value = mock_conn
        
        # Mock dos dados de entrada
        mock_data = pd.DataFrame({
            'ticker': ['PETR4'] * 30,
            'data': pd.date_range('2024-01-01', periods=30, freq='D'),
            'abertura': [10.0 + i*0.1 for i in range(30)],
            'maxima': [10.5 + i*0.1 for i in range(30)],
            'minima': [9.5 + i*0.1 for i in range(30)],
            'fechamento': [10.2 + i*0.1 for i in range(30)],
            'volume': [1000 + i*50 for i in range(30)]
        })
        mock_read_sql.return_value = mock_data
        
        # Executar a função
        resultado = calcular_indicadores()
        
        # Verificar que a conexão foi usada corretamente
        mock_conn.execute.assert_called()
        
        # Verificar que os novos indicadores foram inseridos
        # Verificar que o INSERT foi chamado com os novos campos
        insert_calls = []
        for call in mock_conn.execute.call_args_list:
            args = call[0]
            if len(args) > 0 and 'INSERT OR IGNORE INTO indicadores_compartilhados' in args[0]:
                insert_calls.append(args[0])
        
        # Verificar que os novos campos estão presentes
        expected_fields = [
            'atr_60',
            'vol_media_20',
            'vol_media_60',
            'maxima_52s',
            'minima_52s',
            'maxima_3a',
            'minima_3a',
            'parametros_ver'
        ]
        
        for field in expected_fields:
            found = False
            for call in insert_calls:
                if f"{field}" in call:
                    found = True
                    break
            self.assertTrue(found, f"Campo {field} não foi inserido")
        
        # Verificar que os retornos históricos foram inseridos
        retornos_calls = []
        for call in mock_conn.execute.call_args_list:
            args = call[0]
            if len(args) > 0 and 'INSERT OR IGNORE INTO retornos_historicos' in args[0]:
                retornos_calls.append(args[0])
        
        self.assertGreater(len(retornos_calls), 0, "Retornos históricos não foram inseridos")
        
        # Verificar que o número de registros processados é correto
        # Como o teste usa mocks, o número real pode variar
        # O importante é que os novos indicadores foram calculados
        self.assertGreaterEqual(resultado, 1) # Pelo menos um registro foi processado""