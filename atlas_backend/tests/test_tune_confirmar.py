import io
import json
from unittest.mock import patch, mock_open, MagicMock, call
from fastapi.testclient import TestClient
from atlas_backend.main import app

client = TestClient(app)


# ─── Testes de deprecação dos endpoints antigos ───────────────────────────────

def test_confirmar_regime_retorna_410():
    """confirmar-regime foi deprecado em TUNE v3.1 — deve retornar 410."""
    response = client.post(
        "/delta-chaos/tune/confirmar-regime",
        json={"ticker": "TEST", "regime": "ALTA", "run_id": "run-123"},
    )
    assert response.status_code == 410
    assert "deprecado" in response.json()["detail"].lower()


def test_confirmar_todos_retorna_410():
    """confirmar-todos foi deprecado em TUNE v3.1 — deve retornar 410."""
    response = client.post(
        "/delta-chaos/tune/confirmar-todos",
        json={"ticker": "TEST", "run_id": "run-123"},
    )
    assert response.status_code == 410
    assert "deprecado" in response.json()["detail"].lower()


# ─── Helper para capturar JSON gravado via os.fdopen ─────────────────────────

class _CapturingFile:
    """Simula o file object retornado por os.fdopen, capturando o que json.dump escreve."""

    def __init__(self):
        self._buf = io.StringIO()
        self.captured: dict | None = None

    def write(self, s):
        self._buf.write(s)

    def flush(self):
        pass

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        content = self._buf.getvalue()
        self.captured = json.loads(content) if content else None
        return False


# ─── Testes do novo endpoint confirmar-regime-anomalia ────────────────────────

def _mock_aplicar(dados, regime, regime_dados, run_id, modo):
    """Simulação mínima de _aplicar_regime_no_ativo para os testes."""
    estrategia = regime_dados.get("estrategia_eleita")
    status_calib = regime_dados.get("status_calibracao")
    tp_val   = regime_dados.get("tp_calibrado") if status_calib == "calibrado" else dados.get("take_profit")
    stop_val = regime_dados.get("stop_calibrado") if status_calib == "calibrado" else dados.get("stop_loss")

    if "estrategias" not in dados:
        dados["estrategias"] = {}
    dados["estrategias"][regime] = estrategia

    tp_por_regime   = dados.setdefault("tp_por_regime", {})
    stop_por_regime = dados.setdefault("stop_por_regime", {})
    tp_por_regime[regime]   = tp_val
    stop_por_regime[regime] = stop_val

    if not isinstance(dados.get("historico_config"), list):
        dados["historico_config"] = []
    dados["historico_config"].append({
        "data": "2026-04-29", "modulo": "TUNE v3.1",
        "parametro": f"tp_por_regime.{regime}", "valor_novo": tp_val,
        "motivo": f"Aplicação {modo}",
    })
    dados["historico_config"].append({
        "data": "2026-04-29", "modulo": "TUNE v3.1",
        "parametro": f"stop_por_regime.{regime}", "valor_novo": stop_val,
        "motivo": f"Aplicação {modo}",
    })


def test_confirmar_anomalia_aplicar_grava_estrategia_e_tpstop():
    """acao='aplicar' → grava estratégia + tp_por_regime + stop_por_regime."""
    ticker, run_id, regime = "TEST", "run-v31-001", "ALTA"

    mock_data = {
        "ticker": ticker,
        "take_profit": 0.75,
        "stop_loss": 2.0,
        "historico_config": [],
        "estrategias": {},
        "tune_ranking_estrategia": {
            "_meta": {"run_id": run_id, "versao": "3.1"},
            regime: {
                "confirmado":        False,
                "eleicao_status":    "competitiva",
                "estrategia_eleita": "CSP",
                "status_calibracao": "calibrado",
                "tp_calibrado":      0.80,
                "stop_calibrado":    1.75,
                "anomalia": {"detectada": True, "motivos": ["ir_calibrado=0.3 < ir_minimo=0.5"]},
                "aplicacao": "pendente_anomalia",
            },
        },
    }

    cap = _CapturingFile()

    with patch("atlas_backend.api.routes.delta_chaos.get_paths") as mock_get_paths, \
         patch("builtins.open", mock_open(read_data=json.dumps(mock_data))), \
         patch("atlas_backend.core.terminal_stream.emit_log"), \
         patch("delta_chaos.tune._aplicar_regime_no_ativo", side_effect=_mock_aplicar), \
         patch("atlas_backend.core.event_bus.emit_dc_event"), \
         patch("tempfile.mkstemp", return_value=(100, "/tmp/fake.tmp")), \
         patch("os.fdopen", return_value=cap), \
         patch("os.replace"), \
         patch("os.unlink"):

        mock_get_paths.return_value = {"config_dir": "/fake"}
        response = client.post(
            "/delta-chaos/tune/confirmar-regime-anomalia",
            json={"ticker": ticker, "regime": regime, "run_id": run_id, "acao": "aplicar"},
        )

    assert response.status_code == 200, response.json()
    assert cap.captured is not None

    assert cap.captured["tp_por_regime"][regime] == 0.80
    assert cap.captured["stop_por_regime"][regime] == 1.75
    assert cap.captured["estrategias"][regime] == "CSP"

    ranking = cap.captured["tune_ranking_estrategia"]
    assert ranking[regime]["confirmado"] is True
    assert ranking[regime]["aplicacao"] == "anomalia_aprovada_ceo"


def test_confirmar_anomalia_rejeitar_mantem_ciclo_anterior():
    """acao='rejeitar' → NÃO grava tp_por_regime/stop_por_regime/estrategia."""
    ticker, run_id, regime = "TEST", "run-v31-002", "BAIXA"

    mock_data = {
        "ticker": ticker,
        "take_profit": 0.75,
        "stop_loss": 2.0,
        "historico_config": [],
        "estrategias": {"BAIXA": "BEAR_CALL_SPREAD"},
        "tp_por_regime": {"BAIXA": 0.75},
        "stop_por_regime": {"BAIXA": 2.0},
        "tune_ranking_estrategia": {
            "_meta": {"run_id": run_id, "versao": "3.1"},
            regime: {
                "confirmado":        False,
                "eleicao_status":    "estrutural_fixo",
                "estrategia_eleita": "BEAR_CALL_SPREAD",
                "status_calibracao": "calibrado",
                "tp_calibrado":      1.20,
                "stop_calibrado":    3.00,
                "anomalia": {"detectada": True, "motivos": ["variacao_tp=60.0% > max=30.0%"]},
                "aplicacao": "pendente_anomalia",
            },
        },
    }

    cap = _CapturingFile()

    with patch("atlas_backend.api.routes.delta_chaos.get_paths") as mock_get_paths, \
         patch("builtins.open", mock_open(read_data=json.dumps(mock_data))), \
         patch("atlas_backend.core.terminal_stream.emit_log"), \
         patch("delta_chaos.tune._aplicar_regime_no_ativo") as mock_aplicar, \
         patch("atlas_backend.core.event_bus.emit_dc_event"), \
         patch("tempfile.mkstemp", return_value=(100, "/tmp/fake.tmp")), \
         patch("os.fdopen", return_value=cap), \
         patch("os.replace"), \
         patch("os.unlink"):

        mock_get_paths.return_value = {"config_dir": "/fake"}
        response = client.post(
            "/delta-chaos/tune/confirmar-regime-anomalia",
            json={"ticker": ticker, "regime": regime, "run_id": run_id, "acao": "rejeitar"},
        )

    assert response.status_code == 200, response.json()
    # _aplicar_regime_no_ativo NÃO deve ser chamado na rejeição
    mock_aplicar.assert_not_called()
    assert cap.captured is not None

    # Parâmetros do ciclo anterior devem estar intactos
    assert cap.captured.get("tp_por_regime", {}).get(regime) == 0.75
    assert cap.captured.get("stop_por_regime", {}).get(regime) == 2.0
    assert cap.captured["estrategias"][regime] == "BEAR_CALL_SPREAD"

    ranking = cap.captured["tune_ranking_estrategia"]
    assert ranking[regime]["confirmado"] is True
    assert ranking[regime]["aplicacao"] == "anomalia_rejeitada_ceo"


def test_confirmar_anomalia_regime_sem_anomalia_retorna_400():
    """Regime sem anomalia detectada (aplicado automaticamente) deve retornar 400."""
    ticker, run_id, regime = "TEST", "run-v31-003", "NEUTRO"

    mock_data = {
        "ticker": ticker,
        "take_profit": 0.75,
        "stop_loss": 2.0,
        "historico_config": [],
        "estrategias": {},
        "tune_ranking_estrategia": {
            "_meta": {"run_id": run_id, "versao": "3.1"},
            regime: {
                "confirmado":        False,
                "eleicao_status":    "competitiva",
                "estrategia_eleita": "CSP",
                "anomalia":          {"detectada": False, "motivos": []},
                "aplicacao":         "automatica",
            },
        },
    }

    with patch("atlas_backend.api.routes.delta_chaos.get_paths") as mock_get_paths, \
         patch("builtins.open", mock_open(read_data=json.dumps(mock_data))), \
         patch("atlas_backend.core.terminal_stream.emit_log"):

        mock_get_paths.return_value = {"config_dir": "/fake"}
        response = client.post(
            "/delta-chaos/tune/confirmar-regime-anomalia",
            json={"ticker": ticker, "regime": regime, "run_id": run_id, "acao": "aplicar"},
        )

    assert response.status_code == 400
    assert "não tem anomalia" in response.json()["detail"]


def test_confirmar_anomalia_run_id_invalido_retorna_409():
    """run_id errado deve retornar 409."""
    ticker, run_id, regime = "TEST", "run-v31-001", "ALTA"

    mock_data = {
        "ticker": ticker,
        "take_profit": 0.75,
        "stop_loss": 2.0,
        "historico_config": [],
        "estrategias": {},
        "tune_ranking_estrategia": {
            "_meta": {"run_id": "run-diferente", "versao": "3.1"},
            regime: {
                "confirmado": False,
                "anomalia": {"detectada": True, "motivos": ["ir_calibrado=0.3 < ir_minimo=0.5"]},
            },
        },
    }

    with patch("atlas_backend.api.routes.delta_chaos.get_paths") as mock_get_paths, \
         patch("builtins.open", mock_open(read_data=json.dumps(mock_data))), \
         patch("atlas_backend.core.terminal_stream.emit_log"):

        mock_get_paths.return_value = {"config_dir": "/fake"}
        response = client.post(
            "/delta-chaos/tune/confirmar-regime-anomalia",
            json={"ticker": ticker, "regime": regime, "run_id": run_id, "acao": "aplicar"},
        )

    assert response.status_code == 409


def test_confirmar_anomalia_acao_invalida_retorna_400():
    """acao desconhecida deve retornar 400."""
    response = client.post(
        "/delta-chaos/tune/confirmar-regime-anomalia",
        json={"ticker": "TEST", "regime": "ALTA", "run_id": "run-123", "acao": "ignorar"},
    )
    assert response.status_code == 400
