import unittest
import math
import sys
from pathlib import Path

# Adicionar o caminho do projeto ao sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from advantage.src.data_layer.utils import calcular_temperatura, calcular_temperatura_zscore

class TestTemperaturaFunctions(unittest.TestCase):
    """Testes para as funções de temperatura em utils.py"""

    def test_calcular_temperatura_normal(self):
        """Testa a função calcular_temperatura com valores normais."""
        # Teste com valores positivos
        resultado = calcular_temperatura(1.0, 2.0, 100, 10)
        # esperado: 1.0 * 2.0 * log(100/10) = 2.0 * log(10) ≈ 2.0 * 2.3026 = 4.6052
        self.assertAlmostEqual(resultado, 4.6052, places=4)
        
        # Teste com polaridade negativa
        resultado = calcular_temperatura(-1.0, 2.0, 100, 10)
        self.assertAlmostEqual(resultado, -4.6052, places=4)
        
        # Teste com intensidade negativa
        resultado = calcular_temperatura(1.0, -2.0, 100, 10)
        self.assertAlmostEqual(resultado, -4.6052, places=4)
        
        # Teste com volume_atual menor que volume_tipico
        resultado = calcular_temperatura(1.0, 2.0, 5, 10)
        # esperado: 1.0 * 2.0 * log(0.5) = 2.0 * (-0.6931) = -1.3862
        self.assertAlmostEqual(resultado, -1.3862, places=4)

    def test_calcular_temperatura_volume_zero(self):
        """Testa a função calcular_temperatura com volume_tipico == 0."""
        # Deve retornar 0.0 quando volume_tipico == 0
        resultado = calcular_temperatura(1.0, 2.0, 100, 0)
        self.assertEqual(resultado, 0.0)
        
        # Também deve retornar 0.0 quando volume_atual == 0
        resultado = calcular_temperatura(1.0, 2.0, 0, 10)
        # esperado: 1.0 * 2.0 * log(0) = 2.0 * (-inf) = -inf, mas não é o caso
        # A função não trata volume_atual == 0 como caso especial, apenas volume_tipico == 0
        # Como volume_tipico != 0, deve calcular normalmente
        # log(0) é -inf, então resultado deve ser -inf
        resultado = calcular_temperatura(1.0, 2.0, 0, 10)
        self.assertEqual(resultado, float('-inf'))

    def test_calcular_temperatura_zscore_normal(self):
        """Testa a função calcular_temperatura_zscore com valores normais."""
        # Teste com valores normais
        resultado = calcular_temperatura_zscore(5.0, 3.0, 1.0)
        # esperado: (5.0 - 3.0) / 1.0 = 2.0
        self.assertEqual(resultado, 2.0)
        
        # Teste com temperatura menor que média
        resultado = calcular_temperatura_zscore(1.0, 3.0, 1.0)
        # esperado: (1.0 - 3.0) / 1.0 = -2.0
        self.assertEqual(resultado, -2.0)
        
        # Teste com desvio padrão maior
        resultado = calcular_temperatura_zscore(5.0, 3.0, 2.0)
        # esperado: (5.0 - 3.0) / 2.0 = 1.0
        self.assertEqual(resultado, 1.0)

    def test_calcular_temperatura_zscore_desvpad_zero(self):
        """Testa a função calcular_temperatura_zscore com desvpad_historico == 0."""
        # Deve retornar 0.0 quando desvpad_historico == 0
        resultado = calcular_temperatura_zscore(5.0, 3.0, 0)
        self.assertEqual(resultado, 0.0)
        
        # Também deve retornar 0.0 quando temperatura == media_historica
        resultado = calcular_temperatura_zscore(3.0, 3.0, 0)
        self.assertEqual(resultado, 0.0)""