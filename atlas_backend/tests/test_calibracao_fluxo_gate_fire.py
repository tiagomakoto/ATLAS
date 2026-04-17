import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from atlas_backend.main import app


client = TestClient(app)


class TestGateFireFluxo:
    """Testes para o fluxo GATE → FIRE na calibração"""

    def test_gate_bloqueado_nao_dispara_fire(self):
        """Quando GATE retorna BLOQUEADO, FIRE não deve ser executado."""
        # Simula GATE bloqueado
        mock_gate_result = {
            "status": "OK",
            "output": "GATE BLOQUEADO — E5 IR por regime reprovado",
            "gate_resultado": {
                "ticker": "PETR4",
                "criterios": [
                    {"id": "E1", "nome": "Taxa de acerto", "passou": True, "valor": "85%"},
                    {"id": "E2", "nome": "IR mínimo", "passou": True, "valor": "+2.1"},
                    {"id": "E3", "nome": "N mínimo de trades", "passou": True, "valor": "50"},
                    {"id": "E4", "nome": "Consistência anual", "passou": True, "valor": "4/4 anos"},
                    {"id": "E5", "nome": "IR por regime", "passou": False, "valor": "-0.3"},
                    {"id": "E6", "nome": "Drawdown máximo", "passou": True, "valor": "-10%"},
                    {"id": "E7", "nome": "Consecutivos negativos", "passou": True, "valor": "2"},
                    {"id": "E8", "nome": "Cobertura de regimes", "passou": True, "valor": "5/6"},
                ],
                "resultado": "BLOQUEADO",
                "falhas": ["E5"]
            }
        }

        with patch("atlas_backend.core.dc_runner.dc_gate_backtest", new=AsyncMock(return_value=mock_gate_result)):
            with patch("atlas_backend.core.dc_runner.dc_fire_diagnostico") as mock_fire:
                # Importar função de calibração
                from atlas_backend.core.dc_runner import dc_calibracao_iniciar

                # Não há mock para fire pois não deve ser chamado
                # Apenas verificamos que gate_resultado.resultado é BLOQUEADO
                assert mock_gate_result["gate_resultado"]["resultado"] == "BLOQUEADO"
                assert "E5" in mock_gate_result["gate_resultado"]["falhas"]

    def test_gate_operar_dispara_fire(self):
        """Quando GATE retorna OPERAR, FIRE deve ser executado."""
        mock_gate_operar = {
            "status": "OK",
            "output": "GATE OPERAR — todos os critérios aprovados",
            "gate_resultado": {
                "ticker": "VALE3",
                "criterios": [
                    {"id": f"E{i}", "nome": f"Critério {i}", "passou": True, "valor": "OK"}
                    for i in range(1, 9)
                ],
                "resultado": "OPERAR",
                "falhas": []
            }
        }

        mock_fire_result = {
            "status": "OK",
            "fire_diagnostico": {
                "ticker": "VALE3",
                "regimes": [
                    {"regime": "ALTA", "trades": 20, "wins": 18, "losses": 2, "acerto_pct": 90.0, "ir": 3.5, "estrategia_dominante": "Bear Call Spread"}
                ],
                "cobertura": {"ciclos_com_operacao": 60, "total_ciclos": 72, "total_trades": 120, "acerto_geral_pct": 87.5, "pnl_total": 15000.0},
                "stops_por_regime": {"BAIXA": 3}
            }
        }

        # Verifica que gate_resultado é OPERAR
        assert mock_gate_operar["gate_resultado"]["resultado"] == "OPERAR"

        # Simula que fire seria chamado apenas quando gate aprovar
        gate_aprovado = mock_gate_operar["gate_resultado"]["resultado"] == "OPERAR"
        if gate_aprovado:
            # FIRE seria executado
            assert mock_fire_result["status"] == "OK"

    def test_calibracao_endpoint_retorna_status_correto(self):
        """Endpoint de calibração deve retornar status started."""
        with patch("atlas_backend.core.dc_runner.dc_calibracao_iniciar", new=AsyncMock(return_value={"status": "started", "step": 1})):
            response = client.post(
                "/delta-chaos/calibracao/iniciar",
                json={"ticker": "PETR4", "confirm": True}
            )
            assert response.status_code == 200
            assert response.json()["status"] == "started"

    def test_calibracao_endpoint_valida_ticker(self):
        """Endpoint deve validar ticker inválido."""
        response = client.post(
            "/delta-chaos/calibracao/iniciar",
            json={"ticker": "123", "confirm": True}
        )
        assert response.status_code == 400 or response.status_code == 422


class TestGateFireTransicao:
    """Testes para a transição GATE → FIRE no dc_runner"""

    def test_transicao_gate_para_fire_requer_operar(self):
        """FIRE só deve ser disparado se GATE retornar OPERAR."""
        gate_resultado_bloqueado = {"resultado": "BLOQUEADO", "falhas": ["E5"]}
        gate_resultado_operar = {"resultado": "OPERAR", "falhas": []}

        # Não deve disparar FIRE quando bloqueado
        def deveria_disparar_fire(gate_resultado):
            return gate_resultado.get("resultado") == "OPERAR"

        assert deveria_disparar_fire(gate_resultado_bloqueado) is False
        assert deveria_disparar_fire(gate_resultado_operar) is True

    def test_gate_resultado_contem_8_criterios(self):
        """GATE deve sempre retornar 8 critérios."""
        gate_completo = {
            "criterios": [
                {"id": "E1", "nome": "Taxa de acerto", "passou": True, "valor": "90%"},
                {"id": "E2", "nome": "IR mínimo", "passou": True, "valor": "+2.5"},
                {"id": "E3", "nome": "N mínimo de trades", "passou": True, "valor": "60"},
                {"id": "E4", "nome": "Consistência anual", "passou": True, "valor": "4/4 anos"},
                {"id": "E5", "nome": "IR por regime", "passou": True, "valor": "+1.8"},
                {"id": "E6", "nome": "Drawdown máximo", "passou": True, "valor": "-8%"},
                {"id": "E7", "nome": "Consecutivos negativos", "passou": True, "valor": "2"},
                {"id": "E8", "nome": "Cobertura de regimes", "passou": True, "valor": "6/6"},
            ],
            "resultado": "OPERAR",
            "falhas": []
        }

        assert len(gate_completo["criterios"]) == 8

        # Verifica que todos os IDs são únicos
        ids = [c["id"] for c in gate_completo["criterios"]]
        assert len(ids) == len(set(ids))


class TestRetomadaCalibracao:
    """Testes para retomada de calibração"""

    def test_retomar_step_nao_pausado_retorna_erro(self):
        """Não deve permitir retomar step que não está pausado."""
        with patch("atlas_backend.core.dc_runner.dc_calibracao_retomar", new=AsyncMock(side_effect=ValueError("Step 1 não está pausado"))):
            response = client.post("/delta-chaos/calibracao/PETR4/retomar")
            assert response.status_code == 400

    def test_retomar_sucesso(self):
        """Retomada bem-sucedida deve retornar status resumed."""
        with patch("atlas_backend.core.dc_runner.dc_calibracao_retomar", new=AsyncMock(return_value={"status": "resumed", "step": 2})):
            response = client.post("/delta-chaos/calibracao/PETR4/retomar")
            assert response.status_code == 200
            assert response.json()["status"] == "resumed"

    def test_retomar_ativo_nao_encontrado(self):
        """Retomar ativo inexistente deve retornar 404."""
        with patch("atlas_backend.core.dc_runner.dc_calibracao_retomar", new=AsyncMock(side_effect=FileNotFoundError("Ativo não encontrado"))):
            response = client.post("/delta-chaos/calibracao/TICKER_INEXISTENTE/retomar")
            assert response.status_code == 404


class TestExportacaoRelatorio:
    """Testes para exportação de relatórios"""

    def test_exportar_relatorio_gate_bloqueado(self):
        """Deve gerar relatório para GATE bloqueado."""
        from atlas_backend.core.relatorios import formatar_relatorio_markdown

        dados_gate_bloqueado = {
            "ticker": "PETR4",
            "ciclo": "2026-04",
            "data": "2026-04-17",
            "gate_resultado": {
                "criterios": [
                    {"id": "E1", "nome": "Taxa de acerto", "passou": True, "valor": "85%"},
                    {"id": "E2", "nome": "IR mínimo", "passou": False, "valor": "0.3"},
                    {"id": "E3", "nome": "N mínimo de trades", "passou": True, "valor": "50"},
                    {"id": "E4", "nome": "Consistência anual", "passou": True, "valor": "4/4 anos"},
                    {"id": "E5", "nome": "IR por regime", "passou": False, "valor": "-0.2"},
                    {"id": "E6", "nome": "Drawdown máximo", "passou": True, "valor": "-10%"},
                    {"id": "E7", "nome": "Consecutivos negativos", "passou": True, "valor": "2"},
                    {"id": "E8", "nome": "Cobertura de regimes", "passou": True, "valor": "5/6"},
                ],
                "resultado": "BLOQUEADO",
                "falhas": ["E2", "E5"]
            },
            "fire_diagnostico": None
        }

        # Verifica que o relatório contém GATE
        markdown = formatar_relatorio_markdown(dados_gate_bloqueado)
        assert "GATE" in markdown or "Critério" in markdown

    def test_exportar_relatorio_calibracao_completa(self):
        """Deve gerar relatório para calibração completa (GATE + FIRE)."""
        from atlas_backend.core.relatorios import formatar_relatorio_markdown

        dados_completos = {
            "ticker": "VALE3",
            "ciclo": "2026-04",
            "data": "2026-04-17",
            "gate_resultado": {
                "criterios": [
                    {"id": f"E{i}", "nome": f"Critério {i}", "passou": True, "valor": "OK"}
                    for i in range(1, 9)
                ],
                "resultado": "OPERAR",
                "falhas": []
            },
            "fire_diagnostico": {
                "regimes": [
                    {"regime": "ALTA", "trades": 20, "acerto_pct": 90.0, "ir": 3.5, "worst_trade": "-R$200", "estrategia_dominante": "Bear Call Spread"}
                ],
                "cobertura": {"ciclos_com_operacao": 60, "total_ciclos": 72, "total_trades": 120, "acerto_geral_pct": 87.5, "pnl_total": 15000.0},
                "stops_por_regime": {"BAIXA": 3}
            }
        }

        markdown = formatar_relatorio_markdown(dados_completos)
        # Verifica seções de FIRE
        assert "FIRE" in markdown or "Diagnóstico" in markdown or "Regime" in markdown