import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from atlas_backend.main import app
from atlas_backend.core.delta_chaos_reader import get_gate_resultado


client = TestClient(app)


class TestGateResultadoEndpoint:
    """Testes para GET /ativos/{ticker}/gate-resultado"""

    def test_gate_resultado_retorna_404_quando_ativo_nao_existe(self):
        """Ativo inexistente deve retornar 404."""
        with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", side_effect=FileNotFoundError("Ativo não encontrado")):
            response = client.get("/ativos/TICKER_INEXISTENTE/gate-resultado")
            assert response.status_code == 404

    def test_gate_resultado_retorna_8_criterios(self):
        """Resposta deve conter exatamente 8 critérios."""
        mock_data = {
            "ticker": "PETR4",
            "calibracao": {
                "gate_resultado": {
                    "criterios": [
                        {"id": "E1", "nome": "Taxa de acerto", "passou": True, "valor": "94.2%"},
                        {"id": "E2", "nome": "IR mínimo", "passou": True, "valor": "+3.34"},
                        {"id": "E3", "nome": "N mínimo de trades", "passou": True, "valor": "69"},
                        {"id": "E4", "nome": "Consistência anual", "passou": True, "valor": "4/4 anos"},
                        {"id": "E5", "nome": "IR por regime", "passou": False, "valor": "-0.2"},
                        {"id": "E6", "nome": "Drawdown máximo", "passou": True, "valor": "-12%"},
                        {"id": "E7", "nome": "Consecutivos negativos", "passou": True, "valor": "2"},
                        {"id": "E8", "nome": "Cobertura de regimes", "passou": True, "valor": "5/6"},
                    ],
                    "resultado": "BLOQUEADO",
                    "falhas": ["E5"]
                }
            },
            "historico": [{"ciclo_id": "2026-04"}]
        }
        with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_data):
            response = client.get("/ativos/PETR4/gate-resultado")
            assert response.status_code == 200
            data = response.json()
            assert len(data["criterios"]) == 8

    def test_gate_resultado_retorna_operar_quando_todos_passa(self):
        """Quando todos os critérios passam, resultado deve ser OPERAR."""
        mock_data = {
            "ticker": "VALE3",
            "calibracao": {
                "gate_resultado": {
                    "criterios": [
                        {"id": f"E{i}", "nome": f"Critério {i}", "passou": True, "valor": "OK"}
                        for i in range(1, 9)
                    ],
                    "resultado": "OPERAR",
                    "falhas": []
                }
            },
            "historico": [{"ciclo_id": "2026-04"}]
        }
        with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_data):
            response = client.get("/ativos/VALE3/gate-resultado")
            assert response.status_code == 200
            data = response.json()
            assert data["resultado"] == "OPERAR"
            assert data["falhas"] == []

    def test_gate_resultado_retorna_bloqueado_quando_falha(self):
        """Quando algum critério falha, resultado deve ser BLOQUEADO."""
        mock_data = {
            "ticker": "BBAS3",
            "calibracao": {
                "gate_resultado": {
                    "criterios": [
                        {"id": "E1", "nome": "Taxa de acerto", "passou": True, "valor": "85%"},
                        {"id": "E2", "nome": "IR mínimo", "passou": False, "valor": "0.3"},
                        {"id": "E3", "nome": "N mínimo de trades", "passou": True, "valor": "45"},
                        {"id": "E4", "nome": "Consistência anual", "passou": True, "valor": "3/4 anos"},
                        {"id": "E5", "nome": "IR por regime", "passou": False, "valor": "-0.1"},
                        {"id": "E6", "nome": "Drawdown máximo", "passou": True, "valor": "-8%"},
                        {"id": "E7", "nome": "Consecutivos negativos", "passou": True, "valor": "3"},
                        {"id": "E8", "nome": "Cobertura de regimes", "passou": True, "valor": "4/6"},
                    ],
                    "resultado": "BLOQUEADO",
                    "falhas": ["E2", "E5"]
                }
            },
            "historico": [{"ciclo_id": "2026-04"}]
        }
        with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_data):
            response = client.get("/ativos/BBAS3/gate-resultado")
            assert response.status_code == 200
            data = response.json()
            assert data["resultado"] == "BLOQUEADO"
            assert "E2" in data["falhas"]
            assert "E5" in data["falhas"]

    def test_gate_resultado_contem_ticker_e_ciclo(self):
        """Resposta deve conter ticker e ciclo_id."""
        mock_data = {
            "ticker": "PETR4",
            "calibracao": {
                "gate_resultado": {
                    "criterios": [
                        {"id": f"E{i}", "nome": f"Critério {i}", "passou": True, "valor": "OK"}
                        for i in range(1, 9)
                    ],
                    "resultado": "OPERAR",
                    "falhas": []
                }
            },
            "historico": [{"ciclo_id": "2026-04", "mes_ano": "2026-04"}]
        }
        with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_data):
            response = client.get("/ativos/PETR4/gate-resultado")
            assert response.status_code == 200
            data = response.json()
            assert data["ticker"] == "PETR4"
            assert data["ciclo"] == "2026-04"

    def test_gate_resultado_criterio_contem_campos_obrigatorios(self):
        """Cada critério deve ter id, nome, passou, valor."""
        mock_data = {
            "ticker": "TESTE",
            "calibracao": {
                "gate_resultado": {
                    "criterios": [
                        {"id": "E1", "nome": "Taxa de acerto", "passou": True, "valor": "90%"}
                    ],
                    "resultado": "OPERAR",
                    "falhas": []
                }
            },
            "historico": []
        }
        with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_data):
            response = client.get("/ativos/TESTE/gate-resultado")
            assert response.status_code == 200
            criterio = response.json()["criterios"][0]
            assert "id" in criterio
            assert "nome" in criterio
            assert "passou" in criterio
            assert "valor" in criterio


class TestGateResultadoHelper:
    """Testes para a função get_gate_resultado (helper)"""

    def test_get_gate_resultado_com_dados_armazenados(self):
        """Deve usar dados de calibracao.gate_resultado quando disponíveis."""
        mock_raw = {
            "ticker": "PETR4",
            "calibracao": {
                "gate_resultado": {
                    "criterios": [
                        {"id": "E1", "nome": "Taxa de acerto", "passou": True, "valor": "95%"}
                    ],
                    "resultado": "OPERAR",
                    "falhas": []
                }
            },
            "historico": []
        }
        with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_raw):
            result = get_gate_resultado("PETR4")
            assert result["resultado"] == "OPERAR"
            assert len(result["criterios"]) >= 1

    def test_get_gate_resultado_fallback_quando_sem_dados(self):
        """Deve retornar fallback quando não há dados armazenados."""
        mock_raw = {
            "ticker": "NOVO",
            "calibracao": {},
            "historico_config": [],
            "historico": []
        }
        with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_raw):
            with patch("atlas_backend.core.delta_chaos_reader.compute_gate_criterios", side_effect=Exception("No data")):
                result = get_gate_resultado("NOVO")
                assert "criterios" in result
                assert "resultado" in result
                assert result["resultado"] == "BLOQUEADO"