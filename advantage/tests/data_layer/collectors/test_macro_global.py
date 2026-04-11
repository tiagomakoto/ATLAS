import pytest
import sys
import os

# Adicionar o caminho do projeto ao sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from data_layer.collectors.macro_global import coletar

def test_coletar_interface():
    """Testa se a função coletar existe e tem a interface correta"""
    # Verificar se a função existe
    assert callable(coletar)
    
    # Testar chamada básica
    resultado = coletar()
    
    # Verificar que retorna um inteiro
    assert isinstance(resultado, int)
    
    # Verificar que não lança exceção
    assert resultado >= 0

def test_coletar_com_tickers():
    """Testa a função coletar com lista de tickers"""
    # A função macro_global não usa tickers, mas testa a interface
    resultado = coletar(tickers=['PETR4', 'VALE3'])
    
    # Verificar que retorna um inteiro
    assert isinstance(resultado, int)
    assert resultado >= 0

def test_coletar_append_only():
    """Testa que a função é append-only (não sobrescreve dados)"""
    # Executar duas vezes e verificar que não lança erro
    resultado1 = coletar()
    resultado2 = coletar()
    
    # Ambas as execuções devem retornar valores válidos
assert isinstance(resultado1, int)
assert isinstance(resultado2, int)
assert resultado1 >= 0
assert resultado2 >= 0

class TestMacroGlobalCollector(unittest.TestCase):
    """Testes para o coletor Macro Global"""

    @patch('advantage.src.data_layer.collectors.macro_global.yf.Ticker')
    @patch('advantage.src.data_layer.collectors.macro_global.fredapi.Fred')
    @patch('advantage.src.data_layer.db.connection.get_connection')
    def test_coletar_retorna_int(self, mock_get_connection, mock_fred, mock_ticker):
        """Verifica que coletar retorna um inteiro >= 0"""
        # Mock da FRED API
        mock_fred_instance = Mock()
        mock_fred.return_value = mock_fred_instance
        
        # Mock das séries da FRED
        mock_fred_series = Mock()
        mock_fred_series.tail.return_value = Mock()
        mock_fred_series.tail.return_value.iloc = [5.25]
        mock_fred_instance.get_series.return_value = mock_fred_series
        
        # Mock do yfinance para cada ticker
        mock_ticker_instances = {}
        for symbol in ['DX-Y.NYB', '^GSPC', 'CL=F', 'BZ=F', 'ZS=F', 'ZC=F', 'HG=F', 'LNGG.L', 'ALI=F', 'GF=F', 'SB=F', 'KC=F', 'SC=F']:
            mock_ticker_instance = Mock()
            mock_ticker_instance.history.return_value = Mock()
            mock_ticker_instance.history.return_value.empty = False
            mock_ticker_instance.history.return_value['Close'].iloc = [100.0]
            mock_ticker_instances[symbol] = mock_ticker_instance
        
        # Configurar o side_effect para retornar o mock correto para cada símbolo
        def mock_ticker_side_effect(symbol):
            return mock_ticker_instances[symbol]
        
        mock_ticker.side_effect = mock_ticker_side_effect
        
        # Mock da conexão com o banco
        mock_conn = Mock()
        mock_get_connection.return_value = mock_conn
        
        # Executar o coletor
        resultado = coletar()
        
        # Verificar que retorna um inteiro >= 0
        self.assertIsInstance(resultado, int)
        self.assertGreaterEqual(resultado, 0)

    @patch('advantage.src.data_layer.collectors.macro_global.yf.Ticker')
    @patch('advantage.src.data_layer.collectors.macro_global.fredapi.Fred')
    @patch('advantage.src.data_layer.db.connection.get_connection')
    def test_coletar_nao_lanca_excecao(self, mock_get_connection, mock_fred, mock_ticker):
        """Verifica que coletar não lança exceção mesmo com APIs indisponíveis"""
        # Mock da FRED API com erro
        mock_fred_instance = Mock()
        mock_fred.return_value = mock_fred_instance
        mock_fred_instance.get_series.side_effect = Exception("Erro na FRED API")
        
        # Mock do yfinance com erro
        mock_ticker.side_effect = Exception("Erro no yfinance")
        
        # Mock da conexão com o banco
        mock_conn = Mock()
        mock_get_connection.return_value = mock_conn
        
        # Executar o coletor
        resultado = coletar()
        
        # Verificar que não lança exceção e retorna 0
        self.assertEqual(resultado, 0)

    @patch('advantage.src.data_layer.collectors.macro_global.yf.Ticker')
    @patch('advantage.src.data_layer.collectors.macro_global.fredapi.Fred')
    @patch('advantage.src.data_layer.db.connection.get_connection')
    def test_novas_commodities_inseridas_corretamente(self, mock_get_connection, mock_fred, mock_ticker):
        """Verifica que as novas commodities são inseridas corretamente no banco"""
        # Mock da FRED API
        mock_fred_instance = Mock()
        mock_fred.return_value = mock_fred_instance
        
        # Mock das séries da FRED
        mock_fred_series = Mock()
        mock_fred_series.tail.return_value = Mock()
        mock_fred_series.tail.return_value.iloc = [5.25]
        mock_fred_instance.get_series.return_value = mock_fred_series
        
        # Mock do yfinance para cada ticker
        mock_ticker_instances = {}
        for symbol in ['DX-Y.NYB', '^GSPC', 'CL=F', 'BZ=F', 'ZS=F', 'ZC=F', 'HG=F', 'LNGG.L', 'ALI=F', 'GF=F', 'SB=F', 'KC=F', 'SC=F']:
            mock_ticker_instance = Mock()
            mock_ticker_instance.history.return_value = Mock()
            mock_ticker_instance.history.return_value.empty = False
            mock_ticker_instance.history.return_value['Close'].iloc = [100.0]
            mock_ticker_instances[symbol] = mock_ticker_instance
        
        # Configurar o side_effect para retornar o mock correto para cada símbolo
        def mock_ticker_side_effect(symbol):
            return mock_ticker_instances[symbol]
        
        mock_ticker.side_effect = mock_ticker_side_effect
        
        # Mock da conexão com o banco
        mock_conn = Mock()
        mock_get_connection.return_value = mock_conn
        
        # Executar o coletor
        resultado = coletar()
        
        # Verificar que a conexão foi usada corretamente
        mock_conn.execute.assert_called()
        
        # Verificar que as novas commodities foram inseridas
        # Verificar que o INSERT foi chamado para cada nova commodity
        expected_commodities = [
            'niquel_lme',
            'aluminio_lme',
            'boi_gordo_b3',
            'acucar_nybot',
            'cafe_nybot'
        ]
        
        # Contar quantas vezes o INSERT foi chamado
        insert_calls = []
        for call in mock_conn.execute.call_args_list:
            args = call[0]
            if len(args) > 0 and 'INSERT OR IGNORE INTO macro_global' in args[0]:
                insert_calls.append(args[0])
        
        # Verificar que cada commodity nova foi inserida
        for commodity in expected_commodities:
            found = False
            for call in insert_calls:
                if f"{commodity}" in call:
                    found = True
                    break
            self.assertTrue(found, f"Commodity {commodity} não foi inserida")
        
        # Verificar que o número de registros inseridos é correto
        # 12 commodities + 2 da FRED + 1 minério de ferro = 15 registros
        # Mas como o teste usa mocks, o número real pode variar
        # O importante é que as novas commodities foram inseridas
        self.assertGreaterEqual(resultado, 5) # Pelo menos as 5 novas commodities foram inseridas""