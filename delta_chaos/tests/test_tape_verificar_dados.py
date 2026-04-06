"""
Testes de tape_verificar_dados() — forçam ausência de cada fonte
para validar comportamento de disponibilidade.

IMPORTANTE: os testes manipulam o filesystem temporariamente.
Não executar em produção com dados reais sem backup.
"""
import os
import shutil
import tempfile
import pytest
import pandas as pd
from datetime import date
from unittest.mock import patch

# Ajustar path conforme estrutura do projeto
from delta_chaos.tape import tape_verificar_dados
from delta_chaos.init import COTAHIST_DIR, SELIC_CACHE, OHLCV_DIR


# ── COTAHIST ──────────────────────────────────────────────────────────────────

class TestCotahist:

    def test_disponivel_anual(self, tmp_path, monkeypatch):
        """COTAHIST anual presente e válido → disponivel=True"""
        monkeypatch.setattr("delta_chaos.tape.COTAHIST_DIR", str(tmp_path))
        # Cria arquivo anual com tamanho mínimo (simula arquivo válido)
        txt = tmp_path / "COTAHIST_A2025.TXT"
        txt.write_bytes(b"X" * int(50 * 1e6))  # 50MB
        resultado = tape_verificar_dados("cotahist", ano=2025)
        assert resultado["disponivel"] is True
        assert resultado["motivo"] is None
        assert resultado["tipo"] == "laggeada"

    def test_disponivel_mensal(self, tmp_path, monkeypatch):
        """COTAHIST mensal presente → disponivel=True"""
        monkeypatch.setattr("delta_chaos.tape.COTAHIST_DIR", str(tmp_path))
        txt = tmp_path / "COTAHIST_M042026.TXT"
        txt.write_bytes(b"X" * int(2 * 1e6))  # 2MB
        resultado = tape_verificar_dados("cotahist", ano=2026, mes=4)
        assert resultado["disponivel"] is True

    def test_ausente_retorna_falso(self, tmp_path, monkeypatch):
        """COTAHIST ausente → disponivel=False com motivo legível"""
        monkeypatch.setattr("delta_chaos.tape.COTAHIST_DIR", str(tmp_path))
        # Diretório vazio — nenhum arquivo
        resultado = tape_verificar_dados("cotahist", ano=2026, mes=4)
        assert resultado["disponivel"] is False
        assert "ausente" in resultado["motivo"].lower()
        assert "B3" in resultado["motivo"]

    def test_arquivo_pequeno_invalido(self, tmp_path, monkeypatch):
        """COTAHIST presente mas abaixo do tamanho mínimo → disponivel=False"""
        monkeypatch.setattr("delta_chaos.tape.COTAHIST_DIR", str(tmp_path))
        txt = tmp_path / "COTAHIST_A2026.TXT"
        txt.write_bytes(b"X" * 100)  # 100 bytes — inválido
        resultado = tape_verificar_dados("cotahist", ano=2026)
        assert resultado["disponivel"] is False


# ── SELIC ─────────────────────────────────────────────────────────────────────

class TestSelic:

    def test_disponivel_periodo_coberto(self, tmp_path, monkeypatch):
        """SELIC cache presente e cobrindo o período → disponivel=True"""
        selic_path = tmp_path / "selic_historica.parquet"
        monkeypatch.setattr("delta_chaos.tape.SELIC_CACHE", str(selic_path))
        # Cria cache com dados até dez/2026
        df = pd.DataFrame({
            "data": pd.date_range("2000-01-01", "2026-12-31", freq="B"),
            "selic_aa": [13.5] * len(pd.date_range("2000-01-01", "2026-12-31", freq="B"))
        })
        df.to_parquet(selic_path, index=False)
        resultado = tape_verificar_dados("selic", ano=2026, mes=4)
        assert resultado["disponivel"] is True
        assert resultado["motivo"] is None
        assert resultado["tipo"] == "laggeada"

    def test_ausente_retorna_falso(self, tmp_path, monkeypatch):
        """SELIC cache ausente → disponivel=False com motivo legível"""
        selic_path = tmp_path / "selic_historica.parquet"
        monkeypatch.setattr("delta_chaos.tape.SELIC_CACHE", str(selic_path))
        # Arquivo não existe
        resultado = tape_verificar_dados("selic", ano=2026, mes=4)
        assert resultado["disponivel"] is False
        assert "ausente" in resultado["motivo"].lower()

    def test_cache_desatualizado(self, tmp_path, monkeypatch):
        """SELIC cache presente mas não cobre período solicitado → disponivel=False"""
        selic_path = tmp_path / "selic_historica.parquet"
        monkeypatch.setattr("delta_chaos.tape.SELIC_CACHE", str(selic_path))
        # Cache vai só até mar/2026
        df = pd.DataFrame({
            "data": pd.date_range("2000-01-01", "2026-03-31", freq="B"),
            "selic_aa": [13.5] * len(pd.date_range("2000-01-01", "2026-03-31", freq="B"))
        })
        df.to_parquet(selic_path, index=False)
        resultado = tape_verificar_dados("selic", ano=2026, mes=4)
        assert resultado["disponivel"] is False
        assert "2026" in resultado["motivo"]

    def test_cache_corrompido(self, tmp_path, monkeypatch):
        """SELIC cache corrompido → disponivel=False com motivo legível"""
        selic_path = tmp_path / "selic_historica.parquet"
        monkeypatch.setattr("delta_chaos.tape.SELIC_CACHE", str(selic_path))
        selic_path.write_bytes(b"corrupto")
        resultado = tape_verificar_dados("selic", ano=2026, mes=4)
        assert resultado["disponivel"] is False
        assert "corrompido" in resultado["motivo"].lower()


# ── OHLCV ─────────────────────────────────────────────────────────────────────

class TestOhlcv:

    def test_disponivel_apos_atualizacao(self, monkeypatch):
        """OHLCV tempo-real: mock de tape_ohlcv retornando dados atuais → disponivel=True"""
        df_mock = pd.DataFrame(
            {"close": [100.0]},
            index=pd.to_datetime(["2026-04-01"])
        )
        monkeypatch.setattr("delta_chaos.tape.tape_ohlcv", lambda ticker, anos: df_mock)
        resultado = tape_verificar_dados("ohlcv", ticker="VALE3", ano=2026, mes=4)
        assert resultado["disponivel"] is True
        assert resultado["tipo"] == "tempo_real"

    def test_ausente_apos_tentativa(self, monkeypatch):
        """OHLCV: mock de tape_ohlcv retornando vazio → disponivel=False"""
        monkeypatch.setattr("delta_chaos.tape.tape_ohlcv",
                            lambda ticker, anos: pd.DataFrame())
        resultado = tape_verificar_dados("ohlcv", ticker="VALE3", ano=2026, mes=4)
        assert resultado["disponivel"] is False
        assert "sem dados" in resultado["motivo"].lower()

    def test_desatualizado(self, monkeypatch):
        """OHLCV: dados presentes mas não cobrem o período → disponivel=False"""
        df_mock = pd.DataFrame(
            {"close": [100.0]},
            index=pd.to_datetime(["2026-03-31"])  # só tem até mar
        )
        monkeypatch.setattr("delta_chaos.tape.tape_ohlcv", lambda ticker, anos: df_mock)
        resultado = tape_verificar_dados("ohlcv", ticker="VALE3", ano=2026, mes=4)
        assert resultado["disponivel"] is False
        assert "não coberto" in resultado["motivo"].lower()

    def test_sem_ticker_retorna_falso(self, monkeypatch):
        """OHLCV sem ticker → disponivel=False com motivo claro"""
        resultado = tape_verificar_dados("ohlcv", ticker=None, ano=2026, mes=4)
        assert resultado["disponivel"] is False
        assert "ticker" in resultado["motivo"].lower()

    def test_erro_download(self, monkeypatch):
        """OHLCV: exceção no download → disponivel=False com motivo legível"""
        monkeypatch.setattr("delta_chaos.tape.tape_ohlcv",
                            lambda ticker, anos: (_ for _ in ()).throw(
                                Exception("yfinance timeout")))
        resultado = tape_verificar_dados("ohlcv", ticker="VALE3", ano=2026, mes=4)
        assert resultado["disponivel"] is False
        assert "erro" in resultado["motivo"].lower()


# ── INTERFACE ─────────────────────────────────────────────────────────────────

class TestInterface:

    def test_fonte_desconhecida(self):
        """Fonte não registrada → disponivel=False com lista de fontes válidas"""
        resultado = tape_verificar_dados("bloomberg", ano=2026)
        assert resultado["disponivel"] is False
        assert "cotahist" in resultado["motivo"].lower()

    def test_retorno_sempre_tem_campos_obrigatorios(self, monkeypatch):
        """Qualquer chamada sempre retorna os 5 campos obrigatórios"""
        monkeypatch.setattr("delta_chaos.tape.tape_ohlcv",
                            lambda ticker, anos: pd.DataFrame())
        for fonte, kwargs in [
            ("cotahist", {"ano": 2026, "mes": 4}),
            ("selic",    {"ano": 2026, "mes": 4}),
            ("ohlcv",    {"ticker": "VALE3", "ano": 2026, "mes": 4}),
        ]:
            resultado = tape_verificar_dados(fonte, **kwargs)
            assert "disponivel"  in resultado
            assert "ultima_data" in resultado
            assert "motivo"      in resultado
            assert "fonte"       in resultado
            assert "tipo"        in resultado
