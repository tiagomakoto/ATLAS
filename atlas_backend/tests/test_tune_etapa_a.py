"""
test_tune_etapa_a.py — Testa a lógica da Etapa A (eleição por grid neutro).

_simular_para_candidato é controlada indiretamente: tape vazio → df_dias vazio
→ nenhum pregão → cada simulação retorna {ir_valido: 0.0, trades_valido: 0}.

Sem COTAHIST real, sem Drive, sem ORBIT real. Cada teste < 10s.
"""
import json
import io
from unittest.mock import patch, MagicMock, call
import pandas as pd
import pytest

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

def _cfg(candidatos: dict, estrutural_fixo: dict, n_minimo: int = 15):
    return {
        "tune": {
            "estrategia_n_minimo":   n_minimo,
            "trials_por_candidato":  3,
            "early_stop_patience":   1,
            "startup_trials":        1,
            "janela_anos":           1,
            "n_minimo_calibracao":   99,   # desativa Etapa B nos testes de Etapa A
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


def _ativo_json(regime: str):
    """JSON mínimo do ativo: um ciclo do regime indicado para que ORBIT não precise rodar."""
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
        "tune_ranking_estrategia": {},
    }


def _df_tape_vazio():
    """DataFrame de tape sem pregões → df_dias vazio → 0 trades em todas as simulações."""
    return pd.DataFrame(columns=[
        "data", "ticker", "tipo", "ativo_base",
        "fechamento", "minimo", "maximo", "delta",
        "iv", "T", "volume", "strike", "vencimento",
    ])


class _MockOpen:
    """Simula open() retornando o mesmo JSON em todas as leituras."""

    def __init__(self, ativo_json: dict):
        self._json = ativo_json

    def __call__(self, *args, **kwargs):
        m = MagicMock()
        m.__enter__ = lambda s: io.StringIO(json.dumps(self._json))
        m.__exit__  = MagicMock(return_value=False)
        return m


def _run(cfg: dict, regime: str):
    """
    Executa tune_eleicao_competitiva("TEST") com mocks mínimos.
    Retorna o dicionário de entradas gravadas por regime (chaves = nome do regime).
    """
    ativo = _ativo_json(regime)
    gravados: dict = {}

    def _captura_regime(_path, _regime, entrada):
        gravados[_regime] = entrada

    patches = [
        patch("delta_chaos.tune.carregar_config", return_value=cfg),
        patch("delta_chaos.tune.tape_historico_carregar", return_value=_df_tape_vazio()),
        patch("delta_chaos.tune.tape_ativo_carregar", return_value={}),
        patch("delta_chaos.tune._obter_selic"),
        patch("delta_chaos.tune.tape_externas_carregar", return_value={}),
        patch("delta_chaos.tune.emit_dc_event"),
        patch("delta_chaos.tune._escrever_ativo_atomico", return_value=ativo),
        patch("delta_chaos.tune._escrever_regime_atomico", side_effect=_captura_regime),
        patch("delta_chaos.tune.ATIVOS_DIR", "/fake"),
        patch("builtins.open", _MockOpen(ativo)),
        patch("os.path.join", side_effect=lambda *a: "/fake/TEST.json"),
        patch("os.path.dirname", return_value="/fake"),
    ]

    with patches[0], patches[1], patches[2], patches[3], patches[4], \
         patches[5], patches[6], patches[7], patches[8], \
         patches[9], patches[10], patches[11]:
        tune_eleicao_competitiva("TEST")

    return gravados


# ─── Testes Etapa A ───────────────────────────────────────────────────────────

def test_etapa_a_bloqueado_quando_candidatos_vazios():
    """Regime com candidatos=[] → eleicao_status='bloqueado'."""
    cfg = _cfg(
        candidatos={"BLOQ": []},
        estrutural_fixo={},
        n_minimo=15,
    )
    gravados = _run(cfg, "BLOQ")

    assert "BLOQ" in gravados
    rd = gravados["BLOQ"]
    assert rd["eleicao_status"] == "bloqueado"
    assert rd["estrategia_eleita"] is None
    assert rd["ranking_eleicao"] == []
    assert rd["confirmado"] is False


def test_etapa_a_estrutural_fixo_quando_n_insuficiente():
    """Regime com N_trades_reais=0 < N_MINIMO=15 → eleicao_status='estrutural_fixo'."""
    cfg = _cfg(
        candidatos={"STRUCT": ["CSP"]},
        estrutural_fixo={"STRUCT": "CSP"},
        n_minimo=15,
    )
    # tape vazio → N_trades_reais = 0 em todas as simulações
    gravados = _run(cfg, "STRUCT")

    assert "STRUCT" in gravados
    rd = gravados["STRUCT"]
    assert rd["eleicao_status"] == "estrutural_fixo"
    assert rd["estrategia_eleita"] == "CSP"
    assert rd["n_trades_reais"] == 0
    assert rd["confirmado"] is False
    # ir_eleicao_mediana vem do piloto (N=0 → ir=0.0)
    assert isinstance(rd.get("ir_eleicao_mediana"), (int, float, type(None)))


def test_etapa_a_competitiva_um_candidato():
    """N_MINIMO=0 → competitiva com 1 candidato. Verifica estrutura e mediana do IR."""
    cfg = _cfg(
        candidatos={"COMP1": ["CSP"]},
        estrutural_fixo={"COMP1": "CSP"},
        n_minimo=0,      # garante caminho competitivo independente de N
    )
    gravados = _run(cfg, "COMP1")

    assert "COMP1" in gravados
    rd = gravados["COMP1"]
    assert rd["eleicao_status"] == "competitiva"
    assert rd["estrategia_eleita"] == "CSP"
    assert len(rd["ranking_eleicao"]) == 1
    assert rd["ranking_eleicao"][0]["estrategia"] == "CSP"
    # mediana de 1×1 grid (tudo IR=0.0 pois tape vazio)
    assert rd["ranking_eleicao"][0]["ir_mediana"] == 0.0
    assert rd["confirmado"] is False


def test_etapa_a_competitiva_dois_candidatos_vencedora_por_ir():
    """N_MINIMO=0, 2 candidatos → ranking_eleicao tem 2 entradas ordenadas por ir_mediana."""
    cfg = _cfg(
        candidatos={"COMP2": ["CSP", "BULL_PUT_SPREAD"]},
        estrutural_fixo={"COMP2": "CSP"},
        n_minimo=0,
    )
    # Com tape vazio, ambos retornam ir=0.0.
    # Teste verifica que ambos aparecem no ranking e o primeiro é eleito.
    gravados = _run(cfg, "COMP2")

    assert "COMP2" in gravados
    rd = gravados["COMP2"]
    assert rd["eleicao_status"] == "competitiva"
    assert len(rd["ranking_eleicao"]) == 2

    estrategias_no_ranking = {e["estrategia"] for e in rd["ranking_eleicao"]}
    assert "CSP" in estrategias_no_ranking
    assert "BULL_PUT_SPREAD" in estrategias_no_ranking

    # Vencedora deve ser o primeiro do ranking (ambas IR=0.0, ordem da lista)
    assert rd["estrategia_eleita"] == rd["ranking_eleicao"][0]["estrategia"]

    # ir_mediana deve estar ordenada de forma decrescente
    irs = [e["ir_mediana"] for e in rd["ranking_eleicao"]]
    assert irs == sorted(irs, reverse=True)
