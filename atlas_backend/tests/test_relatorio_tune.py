import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from atlas_backend.main import app
from atlas_backend.core.relatorios import gerar_relatorio_tune

client = TestClient(app)

# Mock target: delta_chaos_reader.get_ativo_raw (imported locally inside gerar_relatorio_tune)
MOCK_TARGET = "atlas_backend.core.delta_chaos_reader.get_ativo_raw"


class TestGerarRelatorioTune:
    """Testes para a funcao gerar_relatorio_tune"""

    def _mock_ativo_com_tune(self):
        return {
            "ticker": "TESTE3",
            "status": "active",
            "core": {"estrategia": "CSP", "regime": "ALTA"},
            "historico": [],
            "historico_config": [
                {
                    "modulo": "TUNE v3.0",
                    "ciclo_id": "2026-04",
                    "data": "2026-04-25",
                    "combinacao": "TP=0.80 STOP=1.50",
                    "valor_novo": "TP=0.80 STOP=1.50",
                    "motivo": "IR=1.45 Alta | N trades: 52 | Trials: 187/200 early stop | TP: 38 STOP: 9 VENC: 5 Acerto: 77.6% | 12 ciclos mascarados de 58 | Ciclos com REFLECT real: 46 | Fallback B: 12",
                    "periodo_teste": "2021-2026",
                    "_meta": {"trials_por_candidato": 200}
                },
                {
                    "modulo": "TUNE v2.0",
                    "ciclo_id": "2026-01",
                    "data": "2026-01-10",
                    "combinacao": "TP=0.75 STOP=1.50",
                    "valor_novo": "TP=0.75 STOP=1.50",
                    "motivo": "IR=1.12 Baixa | N trades: 45 | Trials: 200/200 | TP: 30 STOP: 10 VENC: 5 Acerto: 70.0%",
                    "periodo_teste": "2021-2026",
                    "_meta": {"trials_por_candidato": 200}
                }
            ],
            "take_profit": 0.75,
            "stop_loss": 1.50,
            "reflect_state": "B",
            "calibracao": {"step_atual": 2, "steps": {}}
        }

    def _mock_ativo_sem_tune(self):
        return {
            "ticker": "SEMTUNE3",
            "status": "active",
            "core": {"estrategia": "CSP", "regime": "ALTA"},
            "historico": [],
            "historico_config": [
                {"modulo": "ORBIT v1.0", "ciclo_id": "2026-04", "data": "2026-04-25", "motivo": "Regime ALTA identificado"},
                {"modulo": "GATE v1.0", "ciclo_id": "2026-04", "data": "2026-04-25", "motivo": "GATE OK"}
            ],
            "take_profit": 0.80,
            "stop_loss": 1.50,
            "reflect_state": "B",
            "calibracao": {"step_atual": 1, "steps": {}}
        }

    def test_gerar_relatorio_tune_retorna_payload_com_markdown(self):
        mock_data = self._mock_ativo_com_tune()
        with patch(MOCK_TARGET, return_value=mock_data):
            result = gerar_relatorio_tune("TESTE3")
            assert isinstance(result, dict)
            assert "markdown" in result
            assert result["markdown"] is not None
            assert len(result["markdown"]) > 100

    def test_gerar_relatorio_tune_retorna_historico_tunes_nao_vazio(self):
        mock_data = self._mock_ativo_com_tune()
        with patch(MOCK_TARGET, return_value=mock_data):
            result = gerar_relatorio_tune("TESTE3")
            assert "historico_tunes" in result
            assert isinstance(result["historico_tunes"], list)
            assert len(result["historico_tunes"]) == 2

    def test_gerar_relatorio_tune_historico_true_retorna_todos(self):
        mock_data = self._mock_ativo_com_tune()
        with patch(MOCK_TARGET, return_value=mock_data):
            result = gerar_relatorio_tune("TESTE3", historico=True)
            assert len(result["historico_tunes"]) == 2

    def test_gerar_relatorio_tune_sem_tune_levanta_value_error(self):
        mock_data = self._mock_ativo_sem_tune()
        with patch(MOCK_TARGET, return_value=mock_data):
            with pytest.raises(ValueError) as excinfo:
                gerar_relatorio_tune("SEMTUNE3")
            assert "Nenhum TUNE executado" in str(excinfo.value)

    def test_gerar_relatorio_tune_ativo_inexistente_levanta_file_not_found_error(self):
        with patch(MOCK_TARGET, side_effect=FileNotFoundError("Ativo nao encontrado")):
            with pytest.raises(FileNotFoundError):
                gerar_relatorio_tune("INEXISTENTE")

    def test_gerar_relatorio_tune_campos_obrigatorios_presentes(self):
        mock_data = self._mock_ativo_com_tune()
        with patch(MOCK_TARGET, return_value=mock_data):
            result = gerar_relatorio_tune("TESTE3")
            campos_obrigatorios = [
                "ticker", "ciclo", "data", "tp_atual", "stop_atual",
                "tp_novo", "stop_novo", "delta_tp", "delta_stop",
                "ir_valido", "n_trades", "confianca", "janela_anos",
                "trials_rodados", "trials_total", "early_stop", "retomado",
                "reflect_mask", "total_ciclos", "reflect_mask_pct",
                "ciclos_reais", "ciclos_fallback", "n_tp", "n_stop",
                "n_venc", "acerto_pct", "diagnostico_executivo",
                "historico_tunes", "markdown", "json_completo"
            ]
            for campo in campos_obrigatorios:
                assert campo in result, f"Campo obrigatorio ausente: {campo}"


class TestRotaRelatorioTune:
    """Testes para a rota GET /ativos/{ticker}/relatorio-tune"""

    def _mock_ativo_com_tune(self):
        return {
            "ticker": "TESTE3",
            "status": "active",
            "core": {"estrategia": "CSP", "regime": "ALTA"},
            "historico": [],
            "historico_config": [
                {
                    "modulo": "TUNE v3.0",
                    "ciclo_id": "2026-04",
                    "data": "2026-04-25",
                    "combinacao": "TP=0.80 STOP=1.50",
                    "valor_novo": "TP=0.80 STOP=1.50",
                    "motivo": "IR=1.45 Alta | N trades: 52 | Trials: 187/200 early stop | TP: 38 STOP: 9 VENC: 5 Acerto: 77.6% | 12 ciclos mascarados de 58 | Ciclos com REFLECT real: 46 | Fallback B: 12",
                    "periodo_teste": "2021-2026",
                    "_meta": {"trials_por_candidato": 200}
                }
            ],
            "take_profit": 0.75,
            "stop_loss": 1.50,
            "reflect_state": "B",
            "calibracao": {"step_atual": 2, "steps": {}}
        }

    def _mock_ativo_sem_tune(self):
        return {
            "ticker": "SEMTUNE3",
            "status": "active",
            "core": {"estrategia": "CSP", "regime": "ALTA"},
            "historico": [],
            "historico_config": [
                {"modulo": "ORBIT v1.0", "ciclo_id": "2026-04", "data": "2026-04-25", "motivo": "Regime ALTA"}
            ],
            "take_profit": 0.80,
            "stop_loss": 1.50,
            "reflect_state": "B",
            "calibracao": {"step_atual": 1, "steps": {}}
        }

    def test_rota_retorna_200_quando_tem_tune(self):
        with patch(MOCK_TARGET, return_value=self._mock_ativo_com_tune()):
            response = client.get("/ativos/TESTE3/relatorio-tune")
            assert response.status_code == 200
            data = response.json()
            assert "markdown" in data
            assert data["markdown"] is not None

    def test_rota_retorna_422_quando_sem_tune(self):
        with patch(MOCK_TARGET, return_value=self._mock_ativo_sem_tune()):
            response = client.get("/ativos/SEMTUNE3/relatorio-tune")
            assert response.status_code == 422
            assert "Nenhum TUNE executado" in response.json()["detail"]

    def test_rota_retorna_404_quando_ativo_nao_existe(self):
        with patch(MOCK_TARGET, side_effect=FileNotFoundError("Ativo nao encontrado")):
            response = client.get("/ativos/INEXISTENTE/relatorio-tune")
            assert response.status_code == 404
            assert "encontrado" in response.json()["detail"]

    def test_rota_retorna_500_em_erro_inesperado(self):
        with patch(MOCK_TARGET, side_effect=RuntimeError("Erro inesperado")):
            response = client.get("/ativos/TESTE3/relatorio-tune")
            assert response.status_code == 500
