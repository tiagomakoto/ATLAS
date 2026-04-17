import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from atlas_backend.main import app
from atlas_backend.core.delta_chaos_reader import get_fire_diagnostico


client = TestClient(app)


class TestFireDiagnosticoEndpoint:
    """Testes para GET /ativos/{ticker}/fire-diagnostico"""

    def test_fire_diagnostico_retorna_404_quando_ativo_nao_existe(self):
        """Ativo inexistente deve retornar 404."""
        with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", side_effect=FileNotFoundError("Ativo não encontrado")):
            response = client.get("/ativos/TICKER_INEXISTENTE/fire-diagnostico")
            assert response.status_code == 404

    def test_fire_diagnostico_retorna_regimes(self):
        """Resposta deve conter array de regimes."""
        mock_data = {
            "ticker": "PETR4",
            "calibracao": {
                "fire_diagnostico": {
                    "regimes": [
                        {
                            "regime": "ALTA",
                            "trades": 24,
                            "wins": 23,
                            "losses": 1,
                            "acerto_pct": 95.8,
                            "ir": 4.1,
                            "worst_trade": "-R$320",
                            "best_trade": "+R$890",
                            "avg_win": 145.0,
                            "avg_loss": -320.0,
                            "profit_factor": 2.8,
                            "expectancy": 0.72,
                            "estrategia_dominante": "Bear Call Spread",
                            "estrategias": ["Bear Call Spread", "CSP"],
                            "motivos_saida": {"TP": 15, "STOP": 5, "TIME": 4}
                        },
                        {
                            "regime": "BAIXA",
                            "trades": 18,
                            "wins": 16,
                            "losses": 2,
                            "acerto_pct": 88.9,
                            "ir": 2.7,
                            "worst_trade": "-R$480",
                            "best_trade": "+R$720",
                            "avg_win": 120.0,
                            "avg_loss": -480.0,
                            "profit_factor": 2.1,
                            "expectancy": 0.65,
                            "estrategia_dominante": "Bull Put Spread",
                            "estrategias": ["Bull Put Spread", "CSP"],
                            "motivos_saida": {"TP": 10, "STOP": 6, "TIME": 2}
                        }
                    ],
                    "cobertura": {
                        "ciclos_com_operacao": 69,
                        "total_ciclos": 84,
                        "total_trades": 42,
                        "acerto_geral_pct": 92.9,
                        "pnl_total": 12500.0
                    },
                    "stops_por_regime": {
                        "BAIXA": 4,
                        "ALTA": 2,
                        "NEUTRO_BULL": 1
                    }
                }
            },
            "historico": []
        }
        with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_data):
            response = client.get("/ativos/PETR4/fire-diagnostico")
            assert response.status_code == 200
            data = response.json()
            assert len(data["regimes"]) == 2
            assert data["regimes"][0]["regime"] == "ALTA"
            assert data["regimes"][1]["regime"] == "BAIXA"

    def test_fire_diagnostico_regime_contem_campos_obrigatorios(self):
        """Cada regime deve conter todos os campos obrigatórios."""
        mock_data = {
            "ticker": "VALE3",
            "calibracao": {
                "fire_diagnostico": {
                    "regimes": [
                        {
                            "regime": "ALTA",
                            "trades": 10,
                            "wins": 9,
                            "losses": 1,
                            "acerto_pct": 90.0,
                            "ir": 3.5,
                            "worst_trade": "-R$200",
                            "best_trade": "+R$500",
                            "avg_win": 100.0,
                            "avg_loss": -200.0,
                            "profit_factor": 2.5,
                            "expectancy": 0.8,
                            "estrategia_dominante": "Bear Call Spread",
                            "estrategias": ["Bear Call Spread"],
                            "motivos_saida": {}
                        }
                    ],
                    "cobertura": {"ciclos_com_operacao": 10, "total_ciclos": 12, "total_trades": 10, "acerto_geral_pct": 90.0, "pnl_total": 1000.0},
                    "stops_por_regime": {}
                }
            },
            "historico": []
        }
        with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_data):
            response = client.get("/ativos/VALE3/fire-diagnostico")
            assert response.status_code == 200
            regime = response.json()["regimes"][0]
            assert "regime" in regime
            assert "trades" in regime
            assert "acerto_pct" in regime
            assert "ir" in regime
            assert "worst_trade" in regime
            assert "estrategia_dominante" in regime

    def test_fire_diagnostico_cobertura_contem_campos_obrigatorios(self):
        """Cobertura deve conter ciclos_com_operacao, total_ciclos, total_trades."""
        mock_data = {
            "ticker": "BBAS3",
            "calibracao": {
                "fire_diagnostico": {
                    "regimes": [],
                    "cobertura": {
                        "ciclos_com_operacao": 50,
                        "total_ciclos": 60,
                        "total_trades": 100,
                        "acerto_geral_pct": 85.0,
                        "pnl_total": 5000.0
                    },
                    "stops_por_regime": {}
                }
            },
            "historico": []
        }
        with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_data):
            response = client.get("/ativos/BBAS3/fire-diagnostico")
            assert response.status_code == 200
            cobertura = response.json()["cobertura"]
            assert "ciclos_com_operacao" in cobertura
            assert "total_ciclos" in cobertura
            assert "total_trades" in cobertura

    def test_fire_diagnostico_stops_por_regime(self):
        """Deve retornar distribuição de stops por regime."""
        mock_data = {
            "ticker": "TESTE",
            "calibracao": {
                "fire_diagnostico": {
                    "regimes": [],
                    "cobertura": {"ciclos_com_operacao": 10, "total_ciclos": 12, "total_trades": 10, "acerto_geral_pct": 80.0, "pnl_total": 500.0},
                    "stops_por_regime": {"BAIXA": 5, "ALTA": 2, "NEUTRO_BULL": 1}
                }
            },
            "historico": []
        }
        with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_data):
            response = client.get("/ativos/TESTE/fire-diagnostico")
            assert response.status_code == 200
            data = response.json()
            assert "stops_por_regime" in data
            assert data["stops_por_regime"]["BAIXA"] == 5

    def test_fire_diagnostico_contem_ticker(self):
        """Resposta deve conter ticker."""
        mock_data = {
            "ticker": "PETR4",
            "calibracao": {
                "fire_diagnostico": {
                    "regimes": [],
                    "cobertura": {"ciclos_com_operacao": 0, "total_ciclos": 0, "total_trades": 0, "acerto_geral_pct": 0.0, "pnl_total": 0.0},
                    "stops_por_regime": {}
                }
            },
            "historico": []
        }
        with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_data):
            response = client.get("/ativos/PETR4/fire-diagnostico")
            assert response.status_code == 200
            assert response.json()["ticker"] == "PETR4"


class TestFireDiagnosticoHelper:
    """Testes para a função get_fire_diagnostico (helper)"""

    def test_get_fire_diagnostico_com_dados_armazenados(self):
        """Deve usar dados de calibracao.fire_diagnostico quando disponíveis."""
        mock_raw = {
            "ticker": "PETR4",
            "calibracao": {
                "fire_diagnostico": {
                    "regimes": [{"regime": "ALTA", "trades": 10, "wins": 9, "losses": 1, "acerto_pct": 90.0, "ir": 3.0}],
                    "cobertura": {"ciclos_com_operacao": 10, "total_ciclos": 12, "total_trades": 10, "acerto_geral_pct": 90.0, "pnl_total": 1000.0},
                    "stops_por_regime": {}
                }
            },
            "historico": []
        }
        with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_raw):
            result = get_fire_diagnostico("PETR4")
            assert len(result["regimes"]) == 1
            assert result["regimes"][0]["regime"] == "ALTA"

    def test_get_fire_diagnostico_fallback_vazio(self):
        """Deve retornar fallback mínimo quando não há dados."""
        mock_raw = {
            "ticker": "NOVO",
            "calibracao": {},
            "historico": []
        }
        with patch("atlas_backend.core.delta_chaos_reader.get_ativo_raw", return_value=mock_raw):
            with patch("atlas_backend.core.delta_chaos_reader.compute_fire_diagnostico", side_effect=Exception("No data")):
                result = get_fire_diagnostico("NOVO")
                assert "regimes" in result
                assert "cobertura" in result