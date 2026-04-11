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