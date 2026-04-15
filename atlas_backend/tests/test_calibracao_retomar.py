import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from atlas_backend.main import app


client = TestClient(app)


def test_retomar_step_nao_pausado_retorna_400():
    """Quando dc_calibracao_retomar levanta ValueError, o endpoint deve retornar 400."""
    with patch(
        "atlas_backend.core.dc_runner.dc_calibracao_retomar",
        new=AsyncMock(side_effect=ValueError("Step 1 não está pausado")),
    ):
        response = client.post("/delta-chaos/calibracao/PETR4/retomar")

    assert response.status_code == 400
    assert "não está pausado" in response.json()["detail"]


def test_retomar_arquivo_nao_encontrado_retorna_503():
    """Quando dc_calibracao_retomar levanta FileNotFoundError, o endpoint deve retornar 503."""
    with patch(
        "atlas_backend.core.dc_runner.dc_calibracao_retomar",
        new=AsyncMock(side_effect=FileNotFoundError("Arquivo de estado não encontrado")),
    ):
        response = client.post("/delta-chaos/calibracao/PETR4/retomar")

    assert response.status_code == 503


def test_retomar_sucesso():
    """Quando dc_calibracao_retomar retorna com sucesso, o endpoint repassa o resultado."""
    payload = {"status": "resumed", "step": 2}
    with patch(
        "atlas_backend.core.dc_runner.dc_calibracao_retomar",
        new=AsyncMock(return_value=payload),
    ):
        response = client.post("/delta-chaos/calibracao/PETR4/retomar")

    assert response.status_code == 200
    assert response.json() == payload
