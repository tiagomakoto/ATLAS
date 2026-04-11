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
    assert calcular_variacao_percentual(100, 0) == 0.0  # Divisão por zero