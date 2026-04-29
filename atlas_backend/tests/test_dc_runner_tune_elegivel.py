from unittest.mock import patch
from atlas_backend.core.dc_runner import _tune_elegivel


def test_tune_elegivel_returns_false_when_recent_tune_exists():
    """Testa que _tune_elegivel retorna False quando há TUNE recente (< 126 dias úteis)"""
    mock_dados = {
        "historico_config": [
            {"data": "2026-04-01", "modulo": "TUNE v3.0"},  # Recent date
        ]
    }
    
    with patch("atlas_backend.core.delta_chaos_reader.get_ativo", return_value=mock_dados), \
         patch("atlas_backend.core.dc_runner.date") as mock_date:
        # Mock date.today() to return a date close to 2026-04-01
        from datetime import date
        mock_date.today.return_value = date(2026, 4, 15)  # 10 days later
        
        result = _tune_elegivel("TEST")
        assert result is False  # Not eligible because too recent


def test_tune_elegivel_returns_true_when_no_historico_config():
    """Testa que _tune_elegivel retorna True quando não há historico_config"""
    mock_dados = {
        "historico_config": []  # Empty list
    }
    
    with patch("atlas_backend.core.delta_chaos_reader.get_ativo", return_value=mock_dados):
        result = _tune_elegivel("TEST")
        assert result is True  # Eligible because no history


def test_tune_elegivel_handles_corrupted_historico_config_gracefully():
    """Testa que _tune_elegivel não quebra quando historico_config é bool (dado corrompido)"""
    mock_dados = {
        "historico_config": True  # Corrupted data - bool instead of list
    }
    
    with patch("atlas_backend.core.delta_chaos_reader.get_ativo", return_value=mock_dados):
        result = _tune_elegivel("TEST")
        # Quando historico_config é bool, a função trata como lista vazia e retorna True (elegível)
        assert result is True  # Should treat as no history → eligible


def test_tune_elegivel_returns_true_when_old_tune_exists():
    """Testa que _tune_elegivel retorna True quando há TUNE antigo (> 126 dias úteis)"""
    mock_dados = {
        "historico_config": [
            {"data": "2025-09-01", "modulo": "TUNE v3.0"},  # Old date
        ]
    }
    
    with patch("atlas_backend.core.delta_chaos_reader.get_ativo", return_value=mock_dados), \
         patch("atlas_backend.core.dc_runner.date") as mock_date:
        # Mock date.today() to return a date far in the future
        from datetime import date
        mock_date.today.return_value = date(2026, 4, 15)  # Much later
        
        result = _tune_elegivel("TEST")
        assert result is True  # Eligible because old enough