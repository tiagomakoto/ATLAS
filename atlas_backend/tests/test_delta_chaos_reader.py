import json
from unittest.mock import patch
from atlas_backend.core.delta_chaos_reader import get_ativo
import os


def test_get_ativo_returns_list_for_historico_config():
    """Testa que get_ativo retorna historico_config como lista (não bool)"""
    mock_raw = {
        "ticker": "TEST",
        "historico_config": [
            {"data": "2025-01-15", "modulo": "TUNE v3.0", "parametro": "test"},
            {"data": "2025-01-16", "modulo": "GATE v1.0", "resultado": "APROVADO"}
        ],
        "status": "OK",
        "core": {},
        "historico": [],
        "reflect_historico": [],
        "reflect_state": "B",
        "staleness_days": 0,
        "ultimo_ciclo": "2025-01",
        "version": 1,
        "last_updated": "2025-01-16 10:00:00",
        "take_profit": 0.05,
        "stop_loss": 0.03,
        "calibracao": {"step_atual": 1, "steps": {}}
    }
    
    with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_raw), \
         patch("os.path.exists", return_value=True):
        result = get_ativo("TEST")
        
        # Verifica que historico_config é uma lista
        assert isinstance(result["historico_config"], list)
        # Verifica que contém os dados esperados
        assert len(result["historico_config"]) == 2
        assert result["historico_config"][0]["modulo"] == "TUNE v3.0"
        assert result["historico_config"][1]["modulo"] == "GATE v1.0"


def test_get_ativo_returns_empty_list_when_historico_config_missing():
    """Testa que get_ativo retorna lista vazia quando historico_config está ausente"""
    mock_raw = {
        "ticker": "TEST",
        # historico_config intencionalmente ausente
        "status": "OK",
        "core": {},
        "historico": [],
        "reflect_historico": [],
        "reflect_state": "B",
        "staleness_days": 0,
        "ultimo_ciclo": "2025-01",
        "version": 1,
        "last_updated": "2025-01-16 10:00:00",
        "take_profit": 0.05,
        "stop_loss": 0.03,
        "calibracao": {"step_atual": 1, "steps": {}}
    }
    
    with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_raw), \
         patch("os.path.exists", return_value=True):
        result = get_ativo("TEST")
        
        # Verifica que historico_config é uma lista vazia
        assert isinstance(result["historico_config"], list)
        assert len(result["historico_config"]) == 0


def test_get_ativo_returns_empty_list_when_historico_config_is_not_list():
    """Testa que get_ativo retorna lista vazia quando historico_config não é lista (dado corrompido)"""
    mock_raw = {
        "ticker": "TEST",
        "historico_config": True,  # Dado corrompido - bool em vez de lista
        "status": "OK",
        "core": {},
        "historico": [],
        "reflect_historico": [],
        "reflect_state": "B",
        "staleness_days": 0,
        "ultimo_ciclo": "2025-01",
        "version": 1,
        "last_updated": "2025-01-16 10:00:00",
        "take_profit": 0.05,
        "stop_loss": 0.03,
        "calibracao": {"step_atual": 1, "steps": {}}
    }
    
    with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_raw), \
         patch("os.path.exists", return_value=True):
        result = get_ativo("TEST")
        
        # Verifica que historico_config é uma lista vazia (fallback seguro)
        assert isinstance(result["historico_config"], list)
        assert len(result["historico_config"]) == 0