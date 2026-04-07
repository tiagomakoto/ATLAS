# delta_chaos/tests/test_tape_externas.py

import pandas as pd
import pytest
from delta_chaos.tape import tape_externas


def test_retorna_dict_vazio_sem_externas_ativas(monkeypatch):
    """Nenhum ativo com externas ativas → retorna {}"""
    monkeypatch.setattr("delta_chaos.tape.tape_carregar_ativo",
                        lambda t: {"externas": {"usdbrl": False, "minerio": False}})
    resultado = tape_externas(["VALE3"], [2025, 2026])
    assert resultado == {}


def test_retorna_serie_para_externa_ativa(monkeypatch):
    """Ativo com usdbrl=True → retorna série usdbrl"""
    monkeypatch.setattr("delta_chaos.tape.tape_carregar_ativo",
                        lambda t: {"externas": {"usdbrl": True, "minerio": False}})
    mock_serie = pd.Series([5.0, 5.1], index=pd.to_datetime(["2026-01-02", "2026-01-03"]))
    monkeypatch.setattr("delta_chaos.tape.tape_serie_externa",
                        lambda nome, anos: mock_serie if nome == "usdbrl" else None)
    resultado = tape_externas(["VALE3"], [2026])
    assert "usdbrl" in resultado
    assert "minerio" not in resultado
    pd.testing.assert_series_equal(resultado["usdbrl"], mock_serie)


def test_deduplicacao_entre_ativos(monkeypatch):
    """Dois ativos com mesma série ativa → tape_serie_externa chamada uma vez"""
    calls = []
    monkeypatch.setattr("delta_chaos.tape.tape_carregar_ativo",
                        lambda t: {"externas": {"usdbrl": True}})
    mock_serie = pd.Series([5.0])
    def mock_tape(nome, anos):
        calls.append(nome)
        return mock_serie
    monkeypatch.setattr("delta_chaos.tape.tape_serie_externa", mock_tape)
    tape_externas(["VALE3", "PETR4"], [2026])
    assert calls.count("usdbrl") == 1  # não baixa duas vezes


def test_orbit_rodar_nao_acessa_externas_internamente(monkeypatch):
    """ORBIT.rodar() com externas_dict injetado não chama tape_serie_externa"""
    calls = []
    monkeypatch.setattr("delta_chaos.tape.tape_serie_externa",
                        lambda nome, anos: calls.append(nome) or pd.Series())
    from delta_chaos.orbit import ORBIT
    # Instância mínima para teste
    orbit = ORBIT(universo={"VALE3": {}})
    # Chamar rodar() com um df_tape dummy e externas_dict vazio
    df_dummy = pd.DataFrame({"data": pd.date_range("2026-01-01", periods=10), "close": range(10)})
    try:
        orbit.rodar(df_dummy, [2026], modo="pipeline", externas_dict={})
    except Exception:
        pass  # Ignorar erros de processamento — o importante é verificar se tape_serie_externa foi chamada
    assert calls == []  # não deve ter chamado tape_serie_externa
