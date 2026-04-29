import json
from unittest.mock import patch, mock_open
from fastapi.testclient import TestClient
from atlas_backend.main import app

client = TestClient(app)


def test_confirmar_regime_with_corrupted_historico_config():
    """Testa que o endpoint /tune/confirmar-regime não quebra quando historico_config é bool (dado corrompido)"""
    ticker = "TEST"
    run_id = "test_run_123"
    regime = "ALTA"
    
    # Mock data with corrupted historico_config (bool instead of list)
    mock_data = {
        "ticker": ticker,
        "historico_config": True,  # This is the corruption we want to test
        "tune_ranking_estrategia": {
            "_meta": {
                "run_id": run_id
            },
            regime: {
                "confirmado": False,
                "eleicao_status": "competitiva",
                "ranking": [
                    {"estrategia": "CSP", "score": 0.95}
                ],
                "estrategia_eleita": "CSP"
            }
        },
        "estrategias": {}
    }
    
    # Mock the file read and get_paths
    with patch("atlas_backend.api.routes.delta_chaos.get_paths") as mock_get_paths, \
         patch("builtins.open", mock_open(read_data=json.dumps(mock_data))) as mock_file, \
         patch("atlas_backend.core.terminal_stream.emit_log"), \
         patch("tempfile.mkstemp") as mock_mkstemp, \
         patch("os.fdopen"), \
         patch("os.replace"), \
         patch("os.unlink"):
        
        # Setup mock for tempfile.mkstemp to return a fake file descriptor and path
        mock_mkstemp.return_value = (100, "/tmp/fake.tmp")
        
        # Make the request
        response = client.post(
            "/tune/confirmar-regime",
            json={
                "ticker": ticker,
                "regime": regime,
                "run_id": run_id,
                "confirm": True,
                "description": "Test confirmation"
            }
        )
        
        # The endpoint should not return 500 (internal server error) due to the bool append issue
        # It might return 400, 404, 409, etc. depending on validation, but not 500 from the bug
        assert response.status_code != 500, f"Endpoint returned 500: {response.json()}"
        
        # If it returns 200, we can check that the written data would have a list for historico_config
        # But since we mocked the file write, we can't easily check the content without more mocking.
        # At least we know it didn't crash with AttributeError: 'bool' object has no attribute 'append'


def test_confirmar_todos_with_corrupted_historico_config():
    """Testa que o endpoint /tune/confirmar-todos não quebra quando historico_config é bool (dado corrompido)"""
    ticker = "TEST"
    run_id = "test_run_123"
    
    # Mock data with corrupted historico_config (bool instead of list)
    mock_data = {
        "ticker": ticker,
        "historico_config": True,  # This is the corruption we want to test
        "tune_ranking_estrategia": {
            "_meta": {
                "run_id": run_id
            },
            "ALTA": {
                "confirmado": False,
                "eleicao_status": "competitiva",
                "ranking": [
                    {"estrategia": "CSP", "score": 0.95}
                ],
                "estrategia_eleita": "CSP"
            },
            "BAIXA": {
                "confirmado": False,
                "eleicao_status": "competitiva",
                "ranking": [
                    {"estrategia": "BC", "score": 0.90}
                ],
                "estrategia_eleita": "BC"
            }
        },
        "estrategias": {}
    }
    
    # Mock the file read and get_paths
    with patch("atlas_backend.api.routes.delta_chaos.get_paths") as mock_get_paths, \
         patch("builtins.open", mock_open(read_data=json.dumps(mock_data))) as mock_file, \
         patch("atlas_backend.core.terminal_stream.emit_log"), \
         patch("tempfile.mkstemp") as mock_mkstemp, \
         patch("os.fdopen"), \
         patch("os.replace"), \
         patch("os.unlink"):
        
        # Setup mock for tempfile.mkstemp to return a fake file descriptor and path
        mock_mkstemp.return_value = (100, "/tmp/fake.tmp")
        
        # Make the request
        response = client.post(
            "/tune/confirmar-todos",
            json={
                "ticker": ticker,
                "run_id": run_id,
                "confirm": True,
                "description": "Test bulk confirmation"
            }
        )
        
        # The endpoint should not return 500 (internal server error) due to the bool append issue
        assert response.status_code != 500, f"Endpoint returned 500: {response.json()}"