"""
test_tune_etapa_b.py — Testa a lógica da Etapa B (calibração TP/Stop por Optuna).

Estratégia de isolamento:
  - ativo JSON pré-populado com tune_ranking_estrategia[regime] já em status
    "competitiva" (simulando saída da Etapa A sem rodá-la de verdade).
  - tape vazio → df_dias vazio → _simular_para_candidato retorna
    {ir_valido: 0.0, trades_valido: 0} em toda chamada de N_trades_calibracao.
  - _rodar_optuna_tpstop é função de módulo, mockável diretamente.
  - A Etapa A também roda (N_MINIMO=0 forçada para não bloquear),
    mas seu _escrever_regime_atomico é sobrescrito pelo da Etapa B.
    gravados[regime] ao final reflete exclusivamente a saída da Etapa B.

Sem COTAHIST real, sem Drive, sem ORBIT real. Cada teste < 10s.
"""
import json
import io
from unittest.mock import patch, MagicMock
import pandas as pd

from delta_chaos.tune import tune_eleicao_competitiva

# ─── Fixtures comuns ──────────────────────────────────────────────────────────

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


def _cfg_b(candidatos: dict, estrutural_fixo: dict, n_minimo_calibracao: int):
    return {
        "tune": {
            "estrategia_n_minimo":   0,   # força caminho competitivo na Etapa A
            "trials_por_candidato":  3,
            "early_stop_patience":   1,
            "startup_trials":        1,
            "janela_anos":           1,
            "n_minimo_calibracao":   n_minimo_calibracao,
            "candidatos_por_regime": candidatos,
            "estrategia_estrutural_fixo": estrutural_fixo,
            "referencia_eleicao": {
                "tp_values":   [0.75],
                "stop_values": [2.00],
            },
            "calibracao": {
                "tp":   {"min": 0.75, "max": 0.75, "step": 0.01},
                "stop": {"min": 2.00, "max": 2.00, "step": 0.01},
            },
        },
        "fire": _CFG_FIRE,
        "book": _CFG_BOOK,
    }


def _ativo_com_etapa_a(regime: str, estrategia: str) -> dict:
    """
    JSON do ativo com tune_ranking_estrategia[regime] já em status 'competitiva'.
    Simula o estado do arquivo após a Etapa A ter concluído.
    Inclui take_profit e stop_loss para o caminho fallback_global.
    """
    return {
        "ticker": "TEST",
        "take_profit": 0.75,
        "stop_loss": 2.0,
        "regimes_sizing": {regime: 1.0},
        "historico": [
            {
                "ciclo_id": "2024-01",
                "data_ref": "2024-01-01",
                "regime": regime,
                "ir": 1.0,
                "sizing": 1.0,
            }
        ],
        "reflect_cycle_history": {},
        "estrategias": {},
        "tune_ranking_estrategia": {
            "_meta": {"versao": "3.1", "run_id": "test-run-a"},
            regime: {
                "eleicao_status":    "competitiva",
                "estrategia_eleita": estrategia,
                "n_trades_reais":    0,
                "confirmado":        False,
                "ranking_eleicao":   [{"estrategia": estrategia, "ir_mediana": 0.0}],
                "status_calibracao": None,
                "tp_calibrado":      None,
                "stop_calibrado":    None,
                "ir_calibrado":      None,
            },
        },
    }


def _df_tape_vazio():
    return pd.DataFrame(columns=[
        "data", "ticker", "tipo", "ativo_base",
        "fechamento", "minimo", "maximo", "delta",
        "iv", "T", "volume", "strike", "vencimento",
    ])


class _MockOpen:
    """Simula open() retornando sempre o mesmo JSON."""

    def __init__(self, ativo_json: dict):
        self._json = ativo_json

    def __call__(self, *args, **kwargs):
        m = MagicMock()
        m.__enter__ = lambda s: io.StringIO(json.dumps(self._json))
        m.__exit__  = MagicMock(return_value=False)
        return m


def _run_b(cfg: dict, regime: str, estrategia: str, optuna_retorno=None):
    """
    Executa tune_eleicao_competitiva("TEST") com ativo pré-populado (pós-Etapa A).
    _rodar_optuna_tpstop é mockado com optuna_retorno.
    Retorna o dicionário de entradas gravadas por _escrever_regime_atomico.
    Como a Etapa B sobrescreve as entradas da Etapa A, gravados[regime]
    ao final reflete exclusivamente a saída da Etapa B.
    """
    ativo = _ativo_com_etapa_a(regime, estrategia)
    gravados: dict = {}

    def _captura_regime(_path, _regime, entrada):
        gravados[_regime] = entrada

    _optuna_mock = MagicMock(return_value=optuna_retorno if optuna_retorno is not None
                             else (0.75, 2.0, 0.5, 3))

    patches = [
        patch("delta_chaos.tune.carregar_config", return_value=cfg),
        patch("delta_chaos.tune.tape_historico_carregar", return_value=_df_tape_vazio()),
        patch("delta_chaos.tune.tape_ativo_carregar", return_value={}),
        patch("delta_chaos.tune._obter_selic"),
        patch("delta_chaos.tune.tape_externas_carregar", return_value={}),
        patch("delta_chaos.tune.emit_dc_event"),
        patch("delta_chaos.tune._escrever_ativo_atomico", return_value=ativo),
        patch("delta_chaos.tune._escrever_regime_atomico", side_effect=_captura_regime),
        patch("delta_chaos.tune._rodar_optuna_tpstop", _optuna_mock),
        patch("delta_chaos.tune.ATIVOS_DIR", "/fake"),
        patch("builtins.open", _MockOpen(ativo)),
        patch("os.path.join", side_effect=lambda *a: "/fake/TEST.json"),
        patch("os.path.dirname", return_value="/fake"),
    ]

    with patches[0], patches[1], patches[2], patches[3], patches[4], \
         patches[5], patches[6], patches[7], patches[8], patches[9], \
         patches[10], patches[11], patches[12]:
        tune_eleicao_competitiva("TEST")

    return gravados


# ─── Testes Etapa B ───────────────────────────────────────────────────────────

def test_etapa_b_calibrado_quando_n_suficiente():
    """
    n_minimo_calibracao=0 → N_trades_calib=0 >= 0 → status_calibracao='calibrado'.
    Optuna mockado retorna (tp=0.75, stop=2.0, ir=0.5, trials=3).
    """
    cfg = _cfg_b(
        candidatos={"CALIB": ["CSP"]},
        estrutural_fixo={"CALIB": "CSP"},
        n_minimo_calibracao=0,
    )
    gravados = _run_b(cfg, "CALIB", "CSP", optuna_retorno=(0.75, 2.0, 0.5, 3))

    assert "CALIB" in gravados
    rd = gravados["CALIB"]
    assert rd["status_calibracao"] == "calibrado"
    assert rd["tp_calibrado"] == 0.75
    assert rd["stop_calibrado"] == 2.0
    assert isinstance(rd.get("ir_calibrado"), (int, float, type(None)))
    assert rd.get("trials_rodados") == 3


def test_etapa_b_fallback_global_quando_n_insuficiente():
    """
    n_minimo_calibracao=99 → N_trades_calib=0 < 99 → status_calibracao='fallback_global'.
    Herda take_profit=0.75 e stop_loss=2.0 do JSON do ativo (sem Optuna).
    """
    cfg = _cfg_b(
        candidatos={"FALLB": ["CSP"]},
        estrutural_fixo={"FALLB": "CSP"},
        n_minimo_calibracao=99,
    )
    gravados = _run_b(cfg, "FALLB", "CSP")

    assert "FALLB" in gravados
    rd = gravados["FALLB"]
    assert rd["status_calibracao"] == "fallback_global"
    assert rd["tp_calibrado"] == 0.75    # herdado de ativo["take_profit"]
    assert rd["stop_calibrado"] == 2.0   # herdado de ativo["stop_loss"]
    assert rd.get("ir_calibrado") is None
    assert rd.get("trials_rodados") == 0
