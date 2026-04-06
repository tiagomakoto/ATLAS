# SPEC CIRÚRGICA — tape_verificar_dados()
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board  
**Data:** 2026-04-04  
**Versão:** 1.0  
**Modo:** Cirúrgico — nova função + testes obrigatórios

---

## 1. Localização exata

**Arquivo:** `delta_chaos/tape.py`  
**Inserção:** após as constantes privativas do TAPE (após bloco `SELIC_HISTORICA`), antes de `tape_carregar_ativo()`  
**Funções novas:** `tape_verificar_dados()` + três helpers privados `_check_cotahist()`, `_check_selic()`, `_check_ohlcv()`

---

## 2. Comportamento atual vs comportamento esperado

**Atual:**

Não existe interface unificada de verificação de disponibilidade de dados. Cada módulo tenta baixar e falha silenciosamente ou lança exceção. O orquestrador não tem como saber antecipadamente se os dados necessários estão disponíveis para um determinado ciclo sem tentar executar o processamento completo.

Consequência: `backtest_gate` falha com `ValueError("cobertura mínima insuficiente")` quando COTAHIST do mês corrente ainda não foi liberado pela B3 — erro ambíguo, indistinguível de falha real de configuração.

**Esperado:**

Função pública `tape_verificar_dados(fonte, ticker, ano, mes)` que:
- Encapsula a distinção entre fontes laggeadas (COTAHIST, SELIC) e fontes tempo-real (OHLCV)
- Para fontes laggeadas: verifica apenas cache local — não tenta download
- Para fontes tempo-real: tenta atualizar cache via download antes de responder
- Retorna dict estruturado com `disponivel`, `ultima_data`, `motivo`
- É extensível: adicionar nova fonte requer apenas novo entry em `FONTES` + helper `_check_*`

---

## 3. Constraint crítico — o que não pode ser alterado

- Nenhuma função existente em `tape.py` deve ser modificada
- `_cache_ok()` existente deve ser reutilizado pelos helpers — não reimplementar
- `_obter_selic()`, `tape_ohlcv()`, `_baixar_cotahist()` permanecem inalteradas
- A interface deve aceitar `ticker=None` para fontes que não dependem de ativo (COTAHIST, SELIC)
- A interface deve aceitar `mes=None` para verificações anuais

---

## 4. Implementação esperada

**4.1 — Registro de fontes**

```python
# ── Registro de fontes de dados ──────────────────────────────────────────────
# Extensível: adicionar nova fonte = novo entry aqui + helper _check_*
# tipo "laggeada"   → verifica apenas cache local, não tenta download
# tipo "tempo_real" → tenta atualizar cache antes de responder

_FONTES_DADOS = {
    "cotahist": {"tipo": "laggeada",   "check": "_check_cotahist"},
    "selic":    {"tipo": "laggeada",   "check": "_check_selic"},
    "ohlcv":    {"tipo": "tempo_real", "check": "_check_ohlcv"},
}
```

**4.2 — Helpers privados**

```python
def _check_cotahist(ticker: str, ano: int, mes: int) -> dict:
    """
    Verifica cache local apenas — não tenta download.
    COTAHIST anual tem precedência sobre mensais.
    """
    # Tenta anual
    txt_anual = os.path.join(COTAHIST_DIR, f"COTAHIST_A{ano}.TXT")
    _min_mb = (carregar_config()["tape"]["min_cotahist_mb_antigo"]
               if ano < carregar_config()["tape"]["ano_corte_cotahist"]
               else MIN_COTAHIST_MB)
    if _cache_ok(txt_anual, _min_mb):
        return {
            "disponivel": True,
            "ultima_data": date(ano, 12, 31),
            "motivo": None
        }
    # Tenta mensais — verifica se mês solicitado está presente
    if mes:
        txt_mensal = os.path.join(
            COTAHIST_DIR, f"COTAHIST_M{mes:02d}{ano}.TXT")
        if _cache_ok(txt_mensal, 1.0):
            return {
                "disponivel": True,
                "ultima_data": date(ano, mes, 1),
                "motivo": None
            }
        return {
            "disponivel": False,
            "ultima_data": None,
            "motivo": f"COTAHIST {ano}-{mes:02d} ausente no cache local — aguardar liberação B3"
        }
    # Sem mês específico — verifica se qualquer mensal do ano existe
    for m in range(1, 13):
        txt = os.path.join(COTAHIST_DIR, f"COTAHIST_M{m:02d}{ano}.TXT")
        if _cache_ok(txt, 1.0):
            return {
                "disponivel": True,
                "ultima_data": date(ano, m, 1),
                "motivo": None
            }
    return {
        "disponivel": False,
        "ultima_data": None,
        "motivo": f"COTAHIST {ano} ausente no cache local — aguardar liberação B3"
    }


def _check_selic(ticker: str, ano: int, mes: int) -> dict:
    """
    Verifica cache local apenas — não tenta download.
    SELIC é série diária contínua em selic_historica.parquet.
    """
    if not os.path.exists(SELIC_CACHE):
        return {
            "disponivel": False,
            "ultima_data": None,
            "motivo": "selic_historica.parquet ausente — executar _obter_selic() primeiro"
        }
    try:
        df = pd.read_parquet(SELIC_CACHE)
        df["data"] = pd.to_datetime(df["data"])
        ultima = df["data"].max().date()
        # Verifica se tem dados para o período solicitado
        referencia = date(ano, mes if mes else 12, 1)
        if ultima >= referencia:
            return {
                "disponivel": True,
                "ultima_data": ultima,
                "motivo": None
            }
        return {
            "disponivel": False,
            "ultima_data": ultima,
            "motivo": f"SELIC cache vai até {ultima} — período {ano}-{mes:02d if mes else '??'} não coberto"
        }
    except Exception as e:
        return {
            "disponivel": False,
            "ultima_data": None,
            "motivo": f"selic_historica.parquet corrompido: {e}"
        }


def _check_ohlcv(ticker: str, ano: int, mes: int) -> dict:
    """
    Fonte tempo-real: tenta atualizar cache via yfinance antes de responder.
    Retorna disponível se após tentativa de atualização há dados do período.
    """
    if not ticker:
        return {
            "disponivel": False,
            "ultima_data": None,
            "motivo": "OHLCV requer ticker"
        }
    anos_necessarios = list(range(ano - 1, ano + 1))
    try:
        # tape_ohlcv já incrementa cache se desatualizado
        df = tape_ohlcv(ticker, anos_necessarios)
        if df.empty:
            return {
                "disponivel": False,
                "ultima_data": None,
                "motivo": f"OHLCV {ticker}: sem dados após tentativa de atualização"
            }
        ultima = df.index.max().date()
        referencia = date(ano, mes if mes else 12, 1)
        if ultima >= referencia:
            return {
                "disponivel": True,
                "ultima_data": ultima,
                "motivo": None
            }
        return {
            "disponivel": False,
            "ultima_data": ultima,
            "motivo": f"OHLCV {ticker} vai até {ultima} — período {ano}-{mes if mes else '??'} não coberto"
        }
    except Exception as e:
        return {
            "disponivel": False,
            "ultima_data": None,
            "motivo": f"OHLCV {ticker}: erro ao atualizar — {e}"
        }
```

**4.3 — Interface pública**

```python
def tape_verificar_dados(
    fonte: str,
    ticker: str = None,
    ano: int = None,
    mes: int = None
) -> dict:
    """
    Interface unificada de verificação de disponibilidade de dados.

    Parâmetros:
        fonte:  "cotahist" | "selic" | "ohlcv" | qualquer fonte registrada em _FONTES_DADOS
        ticker: obrigatório para "ohlcv", ignorado para "cotahist" e "selic"
        ano:    ano do período a verificar (default: ano corrente)
        mes:    mês do período a verificar (default: None — verifica o ano inteiro)

    Retorna:
        {
            "disponivel":  bool,
            "ultima_data": date | None,
            "motivo":      str | None,   # preenchido se não disponível
            "fonte":       str,
            "tipo":        "laggeada" | "tempo_real"
        }

    Extensibilidade:
        Para adicionar nova fonte: registrar em _FONTES_DADOS e implementar _check_<fonte>().
        O contrato de retorno do helper deve ser {"disponivel", "ultima_data", "motivo"}.

    Exemplos:
        tape_verificar_dados("cotahist", ano=2026, mes=4)
        tape_verificar_dados("selic", ano=2026, mes=3)
        tape_verificar_dados("ohlcv", ticker="VALE3", ano=2026, mes=4)
    """
    if fonte not in _FONTES_DADOS:
        return {
            "disponivel": False,
            "ultima_data": None,
            "motivo": f"Fonte desconhecida: '{fonte}'. Registradas: {list(_FONTES_DADOS.keys())}",
            "fonte": fonte,
            "tipo": None
        }

    ano = ano or date.today().year
    config_fonte = _FONTES_DADOS[fonte]

    # Despacha para o helper correto
    _check_fn_map = {
        "_check_cotahist": _check_cotahist,
        "_check_selic":    _check_selic,
        "_check_ohlcv":    _check_ohlcv,
    }
    check_fn = _check_fn_map[config_fonte["check"]]
    resultado = check_fn(ticker=ticker, ano=ano, mes=mes)

    return {
        **resultado,
        "fonte": fonte,
        "tipo":  config_fonte["tipo"]
    }
```

---

## 5. Testes obrigatórios

Implementar como script standalone `delta_chaos/tests/test_tape_verificar_dados.py`.  
Executar com `python -m pytest delta_chaos/tests/test_tape_verificar_dados.py -v`.

```python
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
```

---

## 6. Definição de pronto

- `tape_verificar_dados("cotahist", ano=2026, mes=4)` com diretório vazio retorna `disponivel=False` com motivo mencionando "B3"
- `tape_verificar_dados("selic", ano=2026, mes=4)` com cache ausente retorna `disponivel=False` com motivo mencionando "ausente"
- `tape_verificar_dados("ohlcv", ticker="VALE3", ano=2026, mes=4)` com `tape_ohlcv` mockado vazio retorna `disponivel=False`
- `tape_verificar_dados("ohlcv", ticker="VALE3", ano=2026, mes=4)` com `tape_ohlcv` mockado com dados de abr/2026 retorna `disponivel=True`
- Todos os 13 testes passam com `pytest -v`
- Adicionar nova fonte requer apenas: entry em `_FONTES_DADOS` + função `_check_<fonte>()` — sem modificar `tape_verificar_dados()`

---

## 7. Relação com outras specs

Esta spec é um **complemento** da `SPEC_ATLAS_v2.6_orquestrador.md` — que já foi codada e está em fase de teste de campo.

A necessidade de `tape_verificar_dados()` foi identificada em teste real: `gate_eod` não acendia a luz de TAPE no ATLAS porque nunca executa nenhuma função de TAPE que verifique ou atualize dados externos. A SPEC_2.6 não cobriu isso — era impossível antecipar antes do teste de campo.

**O Plan deve aplicar esta spec sobre o código já existente da 2.6 sem modificar o que já funciona.**

O modo CLI `--modo verificar_dados` para o `edge.py` — se necessário para o orquestrador chamar via subprocess — deve ser avaliado pelo Plan no contexto do código já implementado. Se o orquestrador já chama `tape_verificar_dados()` de outra forma, o modo CLI pode não ser necessário.

---

*Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*  
*Spec Cirúrgica v1.0 — 2026-04-04*  
*Complemento da SPEC_ATLAS_v2.6 já implementada — descoberta em teste de campo*
