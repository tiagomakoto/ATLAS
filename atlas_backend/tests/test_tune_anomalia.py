"""
test_tune_anomalia.py — Testa a lógica de gate de anomalia (Etapa C) do TUNE v3.1.

Foco: função _avaliar_anomalia isolada + integração via tune_eleicao_competitiva
(verifica que regimes sem anomalia são aplicados automaticamente e regimes anômalos
ficam com aplicacao='pendente_anomalia').

Sem COTAHIST real, sem Drive, sem ORBIT real. Cada teste < 10s.
"""
import json
import io
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

from delta_chaos.tune import _avaliar_anomalia, tune_eleicao_competitiva

# ─── Testes unitários de _avaliar_anomalia ────────────────────────────────────

def _cfg_anomalia(ir_minimo=0.5, variacao_tp_max=0.30, variacao_stop_max=0.30):
    return {
        "ir_minimo": ir_minimo,
        "variacao_tp_max": variacao_tp_max,
        "variacao_stop_max": variacao_stop_max,
    }

def _regime_calibrado(
    estrategia_eleita="CSP",
    ir_calibrado=1.0,
    tp_calibrado=0.75,
    stop_calibrado=2.0,
    regime_key="ALTA",
):
    rd = {
        "eleicao_status":    "competitiva",
        "estrategia_eleita": estrategia_eleita,
        "status_calibracao": "calibrado",
        "ir_calibrado":      ir_calibrado,
        "tp_calibrado":      tp_calibrado,
        "stop_calibrado":    stop_calibrado,
        "_regime_key":       regime_key,
    }
    return rd

def _ativo(estrategia_atual=None, take_profit=0.75, stop_loss=2.0):
    estrategias = {}
    if estrategia_atual is not None:
        estrategias["ALTA"] = estrategia_atual
    return {
        "take_profit": take_profit,
        "stop_loss":   stop_loss,
        "estrategias": estrategias,
    }


def test_sem_anomalia_quando_tudo_ok():
    """Regime dentro de todos os limites → não é anomalia."""
    rd = _regime_calibrado(ir_calibrado=1.2, tp_calibrado=0.75, stop_calibrado=2.0)
    av = _avaliar_anomalia(rd, _ativo("CSP"), _cfg_anomalia())
    assert av["anomalo"] is False
    assert av["motivos"] == []


def test_anomalia_ir_abaixo_minimo():
    """IR calibrado abaixo de ir_minimo → anomalia."""
    rd = _regime_calibrado(ir_calibrado=0.3)
    av = _avaliar_anomalia(rd, _ativo("CSP"), _cfg_anomalia(ir_minimo=0.5))
    assert av["anomalo"] is True
    assert any("ir_calibrado" in m for m in av["motivos"])


def test_anomalia_variacao_tp_excessiva():
    """Variação de tp_calibrado vs take_profit global acima do máximo → anomalia."""
    # tp_calibrado=1.20, take_profit=0.75 → delta=60% > 30%
    rd = _regime_calibrado(tp_calibrado=1.20, ir_calibrado=1.5)
    av = _avaliar_anomalia(rd, _ativo("CSP", take_profit=0.75), _cfg_anomalia())
    assert av["anomalo"] is True
    assert any("variacao_tp" in m for m in av["motivos"])


def test_anomalia_variacao_stop_excessiva():
    """Variação de stop_calibrado vs stop_loss global acima do máximo → anomalia."""
    # stop_calibrado=3.0, stop_loss=2.0 → delta=50% > 30%
    rd = _regime_calibrado(stop_calibrado=3.0, ir_calibrado=1.5)
    av = _avaliar_anomalia(rd, _ativo("CSP", stop_loss=2.0), _cfg_anomalia())
    assert av["anomalo"] is True
    assert any("variacao_stop" in m for m in av["motivos"])


def test_anomalia_mudanca_estrategia():
    """Estratégia nova diferente da anterior → anomalia."""
    rd = _regime_calibrado(estrategia_eleita="BULL_PUT_SPREAD", ir_calibrado=1.5)
    av = _avaliar_anomalia(rd, _ativo("CSP"), _cfg_anomalia())
    assert av["anomalo"] is True
    assert any("mudanca_estrategia" in m for m in av["motivos"])


def test_anomalia_fallback_global():
    """status_calibracao='fallback_global' → anomalia fixa."""
    rd = _regime_calibrado()
    rd["status_calibracao"] = "fallback_global"
    rd["ir_calibrado"] = None  # fallback não tem IR
    av = _avaliar_anomalia(rd, _ativo("CSP"), _cfg_anomalia())
    assert av["anomalo"] is True
    assert any("fallback_global" in m for m in av["motivos"])


def test_primeira_execucao_sem_estrategia_anterior_nao_e_anomalia():
    """Primeira execução (estrategias={}) → mudança de estratégia NÃO é anomalia."""
    rd = _regime_calibrado(estrategia_eleita="CSP", ir_calibrado=1.5)
    # ativo sem estratégia anterior para esse regime
    av = _avaliar_anomalia(rd, _ativo(estrategia_atual=None), _cfg_anomalia())
    assert av["anomalo"] is False


def test_multiplos_motivos_acumulados():
    """IR baixo + variação TP → dois motivos na lista."""
    rd = _regime_calibrado(ir_calibrado=0.2, tp_calibrado=1.20)
    av = _avaliar_anomalia(rd, _ativo("CSP", take_profit=0.75), _cfg_anomalia())
    assert av["anomalo"] is True
    assert len(av["motivos"]) >= 2


# ─── Integração: Etapa C via tune_eleicao_competitiva ────────────────────────

_CFG_FIRE = {
    "take_profit": 0.75,
    "stop_loss": 2.0,
    "dias_min": 10,
    "dias_max": 45,
    "premio_minimo": 0.05,
    "cooling_off_dias": 5,
    "iv_minimo": 0.10,
    "delta_alvo": {
        "CSP":              {"put_vendida": -0.20},
        "BULL_PUT_SPREAD":  {"put_vendida": -0.25},
        "BEAR_CALL_SPREAD": {"call_vendida": 0.20},
    },
}
_CFG_BOOK = {"risco_trade": 0.02, "fator_margem": 1.0, "n_contratos_minimo": 1}


def _cfg_integracao(ir_minimo=0.5):
    return {
        "tune": {
            "estrategia_n_minimo":   0,
            "trials_por_candidato":  2,
            "early_stop_patience":   1,
            "startup_trials":        1,
            "janela_anos":           1,
            "n_minimo_calibracao":   0,
            "candidatos_por_regime": {"REG": ["CSP"]},
            "estrategia_estrutural_fixo": {"REG": "CSP"},
            "referencia_eleicao": {
                "tp_values":   [0.75],
                "stop_values": [2.00],
            },
            "calibracao": {
                "tp":   {"min": 0.75, "max": 0.75, "step": 0.01},
                "stop": {"min": 2.00, "max": 2.00, "step": 0.01},
            },
            "anomalia": {
                "ir_minimo":        ir_minimo,
                "variacao_tp_max":  0.30,
                "variacao_stop_max": 0.30,
            },
        },
        "fire": _CFG_FIRE,
        "book": _CFG_BOOK,
    }


def _ativo_json(regime: str, estrategia_atual=None):
    estrategias = {}
    if estrategia_atual:
        estrategias[regime] = estrategia_atual
    return {
        "ticker": "TEST",
        "take_profit": 0.75,
        "stop_loss": 2.0,
        "regimes_sizing": {regime: 1.0},
        "historico": [{
            "ciclo_id": "2024-01",
            "data_ref": "2024-01-01",
            "regime": regime,
            "ir": 1.0,
            "sizing": 1.0,
        }],
        "reflect_cycle_history": {},
        "estrategias": estrategias,
        "tune_ranking_estrategia": {},
    }


def _df_tape_vazio():
    return pd.DataFrame(columns=[
        "data", "ticker", "tipo", "ativo_base",
        "fechamento", "minimo", "maximo", "delta",
        "iv", "T", "volume", "strike", "vencimento",
    ])


class _MockOpen:
    def __init__(self, ativo_json):
        self._json = ativo_json

    def __call__(self, *args, **kwargs):
        m = MagicMock()
        m.__enter__ = lambda s: io.StringIO(json.dumps(self._json))
        m.__exit__  = MagicMock(return_value=False)
        return m


class _StatefulMockOpen:
    """
    Simula open() com estado mutável: reflete writes de _escrever_regime_atomico
    para que leituras posteriores (Etapa B, Etapa C) enxerguem o estado atualizado.
    """
    def __init__(self, ativo_base: dict):
        self._state = json.loads(json.dumps(ativo_base))  # deep copy

    def update_regime(self, regime: str, entrada: dict):
        ranking = self._state.setdefault("tune_ranking_estrategia", {})
        ranking[regime] = entrada

    def update_ativo(self, patch_dict: dict):
        self._state.update(patch_dict)

    def current(self) -> dict:
        return json.loads(json.dumps(self._state))  # snapshot imutável

    def __call__(self, *args, **kwargs):
        snap = self.current()
        m = MagicMock()
        m.__enter__ = lambda s: io.StringIO(json.dumps(snap))
        m.__exit__  = MagicMock(return_value=False)
        return m


def _run_integracao(cfg, regime, estrategia_atual=None, optuna_retorno=None):
    """
    Executa tune_eleicao_competitiva com mock stateful:
    _escrever_regime_atomico atualiza o estado do arquivo,
    _escrever_ativo_atomico faz merge e retorna o estado atual.
    Retorna o dict final gravado.
    """
    ativo_base = _ativo_json(regime, estrategia_atual)
    mock_open_obj = _StatefulMockOpen(ativo_base)

    def _captura_regime(_path, _regime, entrada):
        mock_open_obj.update_regime(_regime, entrada)

    def _captura_ativo(_path, patch_dict):
        mock_open_obj.update_ativo(patch_dict)
        return mock_open_obj.current()

    _optuna_mock = MagicMock(
        return_value=optuna_retorno if optuna_retorno is not None else (0.75, 2.0, 1.5, 2)
    )

    patches = [
        patch("delta_chaos.tune.carregar_config", return_value=cfg),
        patch("delta_chaos.tune.tape_historico_carregar", return_value=_df_tape_vazio()),
        patch("delta_chaos.tune.tape_ativo_carregar", return_value={}),
        patch("delta_chaos.tune._obter_selic"),
        patch("delta_chaos.tune.tape_externas_carregar", return_value={}),
        patch("delta_chaos.tune.emit_dc_event"),
        patch("delta_chaos.tune._escrever_ativo_atomico", side_effect=_captura_ativo),
        patch("delta_chaos.tune._escrever_regime_atomico", side_effect=_captura_regime),
        patch("delta_chaos.tune._rodar_optuna_tpstop", _optuna_mock),
        patch("delta_chaos.tune.ATIVOS_DIR", "/fake"),
        patch("builtins.open", mock_open_obj),
        patch("os.path.join", side_effect=lambda *a: "/fake/TEST.json"),
        patch("os.path.dirname", return_value="/fake"),
    ]

    with patches[0], patches[1], patches[2], patches[3], patches[4], \
         patches[5], patches[6], patches[7], patches[8], patches[9], \
         patches[10], patches[11], patches[12]:
        tune_eleicao_competitiva("TEST")

    return mock_open_obj.current()


def test_sem_anomalia_aplica_automatico():
    """IR=1.5 > 0.5, sem mudança de estratégia → aplicação automática."""
    cfg = _cfg_integracao(ir_minimo=0.5)
    gravados = _run_integracao(cfg, "REG", estrategia_atual=None, optuna_retorno=(0.75, 2.0, 1.5, 2))

    assert gravados.get("estrategias", {}).get("REG") == "CSP"
    assert gravados.get("tp_por_regime", {}).get("REG") == 0.75
    assert gravados.get("stop_por_regime", {}).get("REG") == 2.0

    ranking = gravados.get("tune_ranking_estrategia", {})
    assert ranking.get("REG", {}).get("aplicacao") == "automatica"
    assert ranking.get("REG", {}).get("confirmado") is True
    assert ranking.get("REG", {}).get("anomalia", {}).get("detectada") is False


def test_anomalia_ir_baixo_nao_aplica():
    """IR=0.2 < 0.5 → pendente_anomalia, NÃO grava estrategias/tp_por_regime."""
    cfg = _cfg_integracao(ir_minimo=0.5)
    gravados = _run_integracao(cfg, "REG", estrategia_atual=None, optuna_retorno=(0.75, 2.0, 0.2, 2))

    ranking = gravados.get("tune_ranking_estrategia", {})
    assert ranking.get("REG", {}).get("aplicacao") == "pendente_anomalia"
    assert ranking.get("REG", {}).get("confirmado") is False
    assert ranking.get("REG", {}).get("anomalia", {}).get("detectada") is True

    # Estratégia NÃO deve ter sido gravada no ativo operacional
    assert "REG" not in gravados.get("estrategias", {})
    assert "REG" not in gravados.get("tp_por_regime", {})
