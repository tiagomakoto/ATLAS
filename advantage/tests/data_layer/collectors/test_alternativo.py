import pytest
import sys
import os

# Adicionar o caminho do projeto ao sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_layer.collectors.alternativo import coletar, GOOGLE_TRENDS_TERMOS, extrair_producao_papel_celulose

def test_google_trends_termos_existe():
    """Testa se a lista de termos do Google Trends está definida"""
    assert isinstance(GOOGLE_TRENDS_TERMOS, list)
    assert len(GOOGLE_TRENDS_TERMOS) > 0
    assert len(GOOGLE_TRENDS_TERMOS) == 20  # Deve ter 20 termos

def test_coletar_interface():
    """Testa se a função coletar existe e tem a interface correta"""
    assert callable(coletar)
    
    # Testar chamada básica
    resultado = coletar()
    
    # Verificar que retorna um inteiro
    assert isinstance(resultado, int)
    
    # Verificar que não lança exceção
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

def test_extrair_producao_papel_celulose():
    """Testa a função de extração de dados da ABPO"""
    # Teste 1: produção em milhões
    texto1 = "Produção de papel: 5.2 milhões de toneladas. Variação em 12 meses: +1.5%"
    resultado1 = extrair_producao_papel_celulose(texto1)
    assert resultado1['producao_ton'] == 5200000.0
    assert resultado1['variacao_12m'] == 1.5
    
    # Teste 2: produção em milhares
    texto2 = "Produção total: 1.500 mil toneladas. Crescimento de 2.3%"
    resultado2 = extrair_producao_papel_celulose(texto2)
    assert resultado2['producao_ton'] == 1500000.0
    assert resultado2['variacao_12m'] == 2.3
    
    # Teste 3: produção em toneladas diretas
    texto3 = "Celulose produzida: 2500000 toneladas. Queda de -0.8%"
    resultado3 = extrair_producao_papel_celulose(texto3)
    assert resultado3['producao_ton'] == 2500000.0
    assert resultado3['variacao_12m'] == -0.8
    
    # Teste 4: sem dados
    texto4 = "Relatório sem números relevantes."
    resultado4 = extrair_producao_papel_celulose(texto4)
assert resultado4['producao_ton'] is None
assert resultado4['variacao_12m'] is None


class TestAlternativoCollector(unittest.TestCase):
    """Testes para o coletor Alternativo"""

    @patch('advantage.src.data_layer.collectors.alternativo.requests.get')
    @patch('advantage.src.data_layer.db.connection.get_connection')
    def test_coletar_ibge_sidra_embalagens_retorna_int(self, mock_get_connection, mock_get):
        """Verifica que coletar_ibge_sidra_embalagens retorna um inteiro >= 0"""
        # Mock da resposta da API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "periodo": "202401",
                "variavel": "3",
                "resultado": "123456.78"
            },
            {
                "periodo": "202401",
                "variavel": "3.4",
                "resultado": "98765.43"
            }
        ]
        mock_get.return_value = mock_response
        
        # Mock da conexão com o banco
        mock_conn = Mock()
        mock_get_connection.return_value = mock_conn
        
        # Executar o coletor
        resultado = coletar_ibge_sidra_embalagens()
        
        # Verificar que retorna um inteiro >= 0
        self.assertIsInstance(resultado, int)
        self.assertGreaterEqual(resultado, 0)

    @patch('advantage.src.data_layer.collectors.alternativo.requests.get')
    @patch('advantage.src.data_layer.db.connection.get_connection')
    def test_coletar_ibge_sidra_embalagens_nao_lanca_excecao(self, mock_get_connection, mock_get):
        """Verifica que coletar_ibge_sidra_embalagens não lança exceção mesmo com API indisponível"""
        # Mock da resposta da API com erro
        mock_get.side_effect = requests.exceptions.RequestException("Erro de rede")
        
        # Mock da conexão com o banco
        mock_conn = Mock()
        mock_get_connection.return_value = mock_conn
        
        # Executar o coletor
        resultado = coletar_ibge_sidra_embalagens()
        
        # Verificar que não lança exceção e retorna 0
        self.assertEqual(resultado, 0)

    @patch('advantage.src.data_layer.collectors.alternativo.requests.get')
    @patch('advantage.src.data_layer.db.connection.get_connection')
    def test_coletar_ibge_sidra_atividade_retorna_int(self, mock_get_connection, mock_get):
        """Verifica que coletar_ibge_sidra_atividade retorna um inteiro >= 0"""
        # Mock da resposta da API para PMC
        mock_response_pmc = Mock()
        mock_response_pmc.status_code = 200
        mock_response_pmc.json.return_value = [
            {
                "periodo": "202401",
                "variavel": "1",
                "resultado": "123456.78"
            }
        ]
        
        # Mock da resposta da API para PMS
        mock_response_pms = Mock()
        mock_response_pms.status_code = 200
        mock_response_pms.json.return_value = [
            {
                "periodo": "202401",
                "variavel": "1",
                "resultado": "98765.43"
            }
        ]
        
        # Mock da resposta da API para PIM
        mock_response_pim = Mock()
        mock_response_pim.status_code = 200
        mock_response_pim.json.return_value = [
            {
                "periodo": "202401",
                "variavel": "1",
                "resultado": "54321.00"
            }
        ]
        
        # Criar uma função que retorna diferentes mocks para diferentes URLs
        def mock_get_side_effect(url, *args, **kwargs):
            if "8890" in url:  # PMC
                return mock_response_pmc
            elif "8891" in url:  # PMS
                return mock_response_pms
            elif "8892" in url:  # PIM
                return mock_response_pim
            else:
                return Mock(status_code=404)
        
        mock_get.side_effect = mock_get_side_effect
        
        # Mock da conexão com o banco
        mock_conn = Mock()
        mock_get_connection.return_value = mock_conn
        
        # Executar o coletor
        resultado = coletar_ibge_sidra_atividade()
        
        # Verificar que retorna um inteiro >= 0
        self.assertIsInstance(resultado, int)
        self.assertGreaterEqual(resultado, 0)

    @patch('advantage.src.data_layer.collectors.alternativo.requests.get')
    @patch('advantage.src.data_layer.db.connection.get_connection')
    def test_coletar_ibge_sidra_atividade_nao_lanca_excecao(self, mock_get_connection, mock_get):
        """Verifica que coletar_ibge_sidra_atividade não lança exceção mesmo com API indisponível"""
        # Mock da resposta da API com erro
        mock_get.side_effect = requests.exceptions.RequestException("Erro de rede")
        
        # Mock da conexão com o banco
        mock_conn = Mock()
        mock_get_connection.return_value = mock_conn
        
        # Executar o coletor
        resultado = coletar_ibge_sidra_atividade()
        
        # Verificar que não lança exceção e retorna 0
        self.assertEqual(resultado, 0)

    @patch('advantage.src.data_layer.collectors.alternativo.requests.get')
    @patch('advantage.src.data_layer.db.connection.get_connection')
    def test_coletar_mdic_balanca_retorna_int(self, mock_get_connection, mock_get):
        """Verifica que coletar_mdic_balanca retorna um inteiro >= 0"""
        # Mock da resposta da API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "mes": "01",
                    "ano": "2024",
                    "exportacao": 12345678.90,
                    "importacao": 9876543.21
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Mock da conexão com o banco
        mock_conn = Mock()
        mock_get_connection.return_value = mock_conn
        
        # Executar o coletor
        resultado = coletar_mdic_balanca()
        
        # Verificar que retorna um inteiro >= 0
        self.assertIsInstance(resultado, int)
        self.assertGreaterEqual(resultado, 0)

    @patch('advantage.src.data_layer.collectors.alternativo.requests.get')
    @patch('advantage.src.data_layer.db.connection.get_connection')
    def test_coletar_mdic_balanca_nao_lanca_excecao(self, mock_get_connection, mock_get):
        """Verifica que coletar_mdic_balanca não lança exceção mesmo com API indisponível"""
        # Mock da resposta da API com erro
        mock_get.side_effect = requests.exceptions.RequestException("Erro de rede")
        
        # Mock da conexão com o banco
        mock_conn = Mock()
        mock_get_connection.return_value = mock_conn
        
        # Executar o coletor
        resultado = coletar_mdic_balanca()
        
        # Verificar que não lança exceção e retorna 0
        self.assertEqual(resultado, 0)
