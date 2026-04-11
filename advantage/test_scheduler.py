#!/usr/bin/env python3
"""
Teste do scheduler - Tarefa 3
"""
import sys
import os

# Adicionar o caminho do projeto ao sys.path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from src.data_layer.scheduler import calcular_indicadores, log_job_execution
    print('Importação bem-sucedida!')
    
    print('Testando função calcular_indicadores...')
    resultado = calcular_indicadores()
    print(f'Resultado: {resultado} registros processados')
    
    print('Testando função log_job_execution...')
    log_job_execution('teste', 10)
    log_job_execution('teste_erro', 0, 'erro de teste')
    
    print('Teste concluído com sucesso!')
except Exception as e:
    print(f'Erro: {e}')
    import traceback
    traceback.print_exc()