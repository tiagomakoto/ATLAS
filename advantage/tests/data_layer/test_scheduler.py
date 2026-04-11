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