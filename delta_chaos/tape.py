# ════════════════════════════════════════════════════════════════════
import json
import os
import time
# DELTA CHAOS — TAPE v2.0
# Alterações em relação à v1.2:
# MIGRADO (P2): imports explícitos de init — sem escopo global do notebook
# MIGRADO (P5): prints de inicialização sob if __name__ == "__main__"
# MANTIDO: toda a lógica, REFLECT, Black-Scholes, COTAHIST, master JSON
# ════════════════════════════════════════════════════════════════════

from delta_chaos.init import (
    carregar_config, cfg_global,
    ATIVOS_DIR, TAPE_DIR, COTAHIST_DIR, GREGAS_DIR,
    OHLCV_DIR, EXTERNAS_DIR, SELIC_CACHE, BOOK_DIR,
    DRIVE_BASE,
)

# ── Logging ATLAS (graceful fallback) ─────────────────────────────────
try:
    from atlas_backend.core.terminal_stream import emit_log, emit_error
    _atlas_disponivel = True
except ImportError:
    def emit_log(msg, level="info"): print(f"[{level.upper()}] {msg}")
    def emit_error(e): print(f"[ERROR] {e}")
    _atlas_disponivel = False

# DELTA CHAOS — TAPE v2.0
# Alterações em relação à v1.2:
# MIGRADO (P2): imports explícitos de init — sem escopo global do notebook
# MIGRADO (P5): prints de inicialização sob if __name__ == "__main__"
# MANTIDO: toda a lógica de dados, Black-Scholes, COTAHIST, master JSON
# REFLECT: funções movidas para EDGE (reflect_daily_calcular, reflect_cycle_calcular, reflect_sizing_calcular)
# ════════════════════════════════════════════════════════════════════

import os, io, json, math, zipfile, warnings
import urllib.request
from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd
import yfinance as yf
warnings.filterwarnings("ignore")

from scipy.stats import norm as _norm
from tqdm.auto import tqdm as _tqdm

# ════════════════════════════════════════════════════════════════════
# CONSTANTES PRIVATIVAS DO TAPE
# Caminhos vêm do escopo da Célula 1 — não redeclarar aqui
# ════════════════════════════════════════════════════════════════════
SCHEMA_VERSION  = "1.0"
COTAHIST_URL    = "https://bvmf.bmfbovespa.com.br/InstDados/SerHist"
BCB_SELIC_URL   = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados"

_cfg_tape       = carregar_config()["tape"]
MIN_COTAHIST_MB = _cfg_tape["min_cotahist_mb"]
MIN_GREGAS_MB   = _cfg_tape["min_gregas_mb"]
IV_RANK_JANELA  = _cfg_tape["iv_rank_janela"]
LOTE_IV         = _cfg_tape["lote_iv"]

TPMERC_ACAO     = "010"
TPMERC_CALL     = "070"
TPMERC_PUT      = "080"
TICKER_IBOV     = "^BVSP"

PRIOR_PADRAO = {
    "tendencia": 0.20,
    "momentum":  0.20,
    "volume":    0.20,
    "vol_skew":  0.20,
    "macro":     0.20
}

SELIC_HISTORICA = {
    2000: 17.4, 2001: 17.3, 2002: 19.4, 2003: 23.3,
    2004: 16.2, 2005: 19.1, 2006: 15.0, 2007: 12.0,
    2008: 12.4, 2009:  9.9, 2010:  9.9, 2011: 11.8,
    2012:  8.6, 2013:  8.6, 2014: 11.0, 2015: 13.3,
    2016: 14.0, 2017:  9.7, 2018:  6.5, 2019:  5.7,
    2020:  2.5, 2021:  7.7, 2022: 12.8, 2023: 13.5,
    2024: 10.8, 2025: 13.7, 2026: 14.3,
}

# ── Registro de fontes de dados ──────────────────────────────────────────────
# Extensível: adicionar nova fonte = novo entry aqui + helper _check_*
# tipo "laggeada"   → verifica apenas cache local, não tenta download
# tipo "tempo_real" → tenta atualizar cache antes de responder

_FONTES_DADOS = {
    "cotahist": {"tipo": "laggeada",   "check": "_check_cotahist"},
    "selic":    {"tipo": "laggeada",   "check": "_check_selic"},
    "ohlcv":    {"tipo": "tempo_real", "check": "_check_ohlcv"},
}


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
        mes_str = f"{mes:02d}" if mes else "??"
        return {
            "disponivel": False,
            "ultima_data": ultima,
            "motivo": f"SELIC cache vai até {ultima} — período {ano}-{mes_str} não coberto"
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
        # tape_ohlcv_carregar já incrementa cache se desatualizado
        df = tape_ohlcv_carregar(ticker, anos_necessarios)
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


def tape_dados_verificar(
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
        tape_dados_verificar("cotahist", ano=2026, mes=4)
        tape_dados_verificar("selic", ano=2026, mes=3)
        tape_dados_verificar("ohlcv", ticker="VALE3", ano=2026, mes=4)
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


# ════════════════════════════════════════════════════════════════════
# MASTER JSON — leitura e escrita por ativo
# ════════════════════════════════════════════════════════════════════

def tape_ativo_carregar(ticker: str) -> dict:
    ticker = ticker.replace(".SA", "").upper()
    path   = os.path.join(ATIVOS_DIR, f"{ticker}.json")

    _estrategias_padrao = {
        "ALTA":         "CSP",
        "LATERAL_BULL": "BULL_PUT_SPREAD",
        "LATERAL_BEAR": "BEAR_CALL_SPREAD",
        "LATERAL":      None,
        "BAIXA":        None,
        "RECUPERACAO":  None,
        "PANICO":       None,
    }

    default_config = {
        "ativo":                        ticker,
        "foco":                         "",
        "externas": {
            "usdbrl":                   False,
            "minerio":                  False,
        },
        "prior": {
            "tendencia":                0.20,
            "momentum":                 0.20,
            "volume":                   0.20,
            "vol_skew":                 0.20,
            "macro":                    0.20,
        },
        "historico":                    [],
        "historico_config":             [],
        "reflect_state":                "B",
        "reflect_score":                0.0,
        "reflect_history":              [],
        "reflect_daily_history":        {},
        "reflect_all_cycles_history":   [],
        "estrategias":                  _estrategias_padrao.copy(),
        "criado_em":                    str(datetime.now())[:19],
        "atualizado_em":                str(datetime.now())[:19],
    }

    if os.path.exists(path):
        # Tentativa de leitura com retry para evitar race condition durante escrita atômica
        max_retries = 3
        retry_delay = 0.1  # 100ms
        
        for attempt in range(max_retries):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    dados = json.load(f)

                # Migração — garante que todos os campos novos existam
                for key, val in default_config.items():
                    if key not in dados:
                        dados[key] = val

                # Garante sub-regimes em estrategias
                if "estrategias" not in dados:
                    dados["estrategias"] = _estrategias_padrao.copy()
                else:
                    for regime, estrategia in \
                            _estrategias_padrao.items():
                        if regime not in dados["estrategias"]:
                            dados["estrategias"][regime] = estrategia

                return dados

            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                # Erros de decodificação indicam possível corrupção ou leitura durante escrita
                if attempt < max_retries - 1:
                    # Tentativa falhou, aguardar e tentar novamente
                    time.sleep(retry_delay)
                    continue
                else:
                    # Última tentativa falhou - tratar como corrupção real
                    import shutil
                    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
                    bak = os.path.join(
                        ATIVOS_DIR,
                        f"{ticker}_corrupto_{ts}.json")
                    try:
                        shutil.copy2(path, bak)
                        print(f"  ⚠ S2: {ticker}.json corrompido — "
                              f"backup: {os.path.basename(bak)}")
                    except Exception as e2:
                        print(f"  ⚠ S2: backup falhou: {e2}")
                    print(f"  ⚠ S2: propagando erro de leitura após {max_retries} tentativas — "
                          f"erro: {e}")
                    raise  # Propaga a exceção para o chamador tratar
            except Exception as e:
                # Outros erros (permissão, etc.) - propagar imediatamente
                import shutil
                ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
                bak = os.path.join(
                    ATIVOS_DIR,
                    f"{ticker}_corrupto_{ts}.json")
                try:
                    shutil.copy2(path, bak)
                    print(f"  ⚠ S2: {ticker}.json corrompido — "
                          f"backup: {os.path.basename(bak)}")
                except Exception as e2:
                    print(f"  ⚠ S2: backup falhou: {e2}")
                print(f"  ⚠ S2: propagando erro de leitura — "
                      f"erro: {e}")
                raise  # Propaga a exceção para o chamador tratar
    else:
        # Arquivo não existe — cria com defaults completos
        tape_ativo_salvar(ticker, default_config)
        print(f" + Master JSON {ticker} criado com defaults")
        return default_config


def tape_ativo_inicializar(ticker: str) -> dict:
    """
    Garante que o master JSON do ativo existe e tem todos os campos
    obrigatórios preenchidos com valores padrão.
    Idempotente — seguro chamar múltiplas vezes.
    """
    json_path = os.path.join(ATIVOS_DIR, f"{ticker}.json")

    # Carrega existente ou cria vazio
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        cfg = {}
        print(f"  ~ {ticker}: master JSON não encontrado — criando")

    cfg_global = carregar_config()
    alterado   = False

    # ── Campos obrigatórios com fallback ─────────────────────────
    defaults = {
        "ticker":       ticker,
        "take_profit":  cfg_global["fire"]["take_profit"],
        "stop_loss":    cfg_global["fire"]["stop_loss"],
        "historico":    [],
        "externas":     {"usdbrl": False, "minerio": False},

        "estrategias": {
            "ALTA":         "CSP",
            "LATERAL_BULL": "BULL_PUT_SPREAD",
            "LATERAL_BEAR": "BEAR_CALL_SPREAD",
            "LATERAL":      None,
            "BAIXA":        None,
            "RECUPERACAO":  None,
            "PANICO":       None,
        },

        # REFLECT
        "reflect_state":                "B",
        "reflect_score":                0.0,
        "reflect_history":              [],
        "reflect_all_cycles_history":   [],
        "reflect_daily_history":        {},
    }

    for campo, valor in defaults.items():
        if campo not in cfg:
            cfg[campo] = valor
            alterado = True
        elif campo == "estrategias":
            # Garante que todos os regimes existem
            for regime, estrategia in valor.items():
                if regime not in cfg[campo]:
                    cfg[campo][regime] = estrategia
                    alterado = True

    if alterado:
        tape_ativo_salvar(ticker, cfg)
        print(f"  ✓ {ticker}: master JSON inicializado/atualizado")
    else:
        print(f"  ✓ {ticker}: master JSON OK")

    return cfg

def tape_ativo_salvar(ticker: str, cfg_data: dict) -> None:
    """
    Salva master JSON de forma atômica.
    Escreve em .tmp e faz os.replace() — evita JSON truncado
    se a sessão for interrompida durante a escrita.
    SCAN-8: criticidade alta com reflect_state.
    """
    ticker = ticker.replace(".SA","").upper()
    path   = os.path.join(ATIVOS_DIR, f"{ticker}.json")
    path_tmp = path + ".tmp"

    cfg_data["atualizado_em"] = str(datetime.now())[:19]

    with open(path_tmp, "w", encoding="utf-8") as f:
        json.dump(cfg_data, f, indent=2,
                  ensure_ascii=False, default=str)
    os.replace(path_tmp, path)  # atômico no mesmo filesystem


def tape_ciclo_salvar(ticker: str, resultado: dict) -> None:
    ticker = ticker.replace(".SA", "").upper()
    path   = os.path.join(ATIVOS_DIR, f"{ticker}.json")

    # Lê estado atual usando carregador robusto
    dados = tape_ativo_carregar(ticker)

    # Atualiza histórico
    ciclo_id = resultado.get("ciclo_id")
    registro_existente = next(
        (c for c in dados["historico"] if c.get("ciclo_id") == ciclo_id),
        {}
    )
    if registro_existente.get("definitivo", True):
        # Substituir existente (definitivo ou sem campo)
        dados["historico"] = [
            c for c in dados["historico"]
            if c.get("ciclo_id") != ciclo_id
        ]
    else:
        # Remover não-definitivo e adicionar novo
        dados["historico"] = [
            c for c in dados["historico"]
            if c.get("ciclo_id") != ciclo_id
        ]
    dados["historico"].append(resultado)
    dados["historico"].sort(key=lambda x: x["ciclo_id"])
    dados["atualizado_em"] = str(datetime.now())[:19]

    # B24 — escrita atômica via tempfile + os.replace
    # Garante que o arquivo original só é substituído
    # quando o novo está completamente escrito no disco.
    dir_ = os.path.dirname(path)
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(
                "w", dir=dir_, suffix=".tmp",
                delete=False, encoding="utf-8") as tf:
            json.dump(dados, tf, indent=2,
                      ensure_ascii=False, default=str)
            tmp_path = tf.name
        os.replace(tmp_path, path)
    except Exception as e:
        # Limpa temp se existir
        try:
            if 'tmp_path' in locals() and \
               os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        print(f"  ✗ B24: tape_ciclo_salvar falhou — {e}")
        raise

def tape_ciclo_para_data(ticker: str, data: str) -> dict:
    ticker = ticker.replace(".SA","").upper()
    dados  = tape_ativo_carregar(ticker)

    historico = dados.get("historico", [])
    if not historico:
        return {"ciclo": "N/A", "regime": "DESCONHECIDO",
                "ir": 0.0, "sizing": 0.0}

    mes_ref = data[:7]
    validos = [c for c in historico
               if c.get("ciclo_id","") <= mes_ref]
    if not validos:
        return {"ciclo": "N/A", "regime": "DESCONHECIDO",
                "ir": 0.0, "sizing": 0.0}

    ultimo = validos[-1]
    return {
        "ciclo":  ultimo["ciclo_id"],
        "regime": ultimo["regime"],
        "ir":     float(ultimo.get("ir", 0.0)),
        "sizing": float(ultimo.get("sizing", 0.0)),
    }



# ════════════════════════════════════════════════════════════════════
# OHLCV — download e cache via yfinance
# ════════════════════════════════════════════════════════════════════

def tape_ohlcv_carregar(ativo: str, anos: list) -> pd.DataFrame:
    ativo      = ativo.replace(".SA","").upper()
    cache_path = os.path.join(OHLCV_DIR, f"{ativo}.parquet")
    ano_ini    = min(anos) - 2
    ano_fim    = max(anos)

    if os.path.exists(cache_path):
        try:
            df = pd.read_parquet(cache_path)
            df.index = pd.to_datetime(df.index)
            if (df.index.year.min() <= ano_ini and
                    df.index.year.max() >= ano_fim):
                print(f"  ✓ OHLCV cache {ativo}: "
                      f"{len(df):,} dias")
                return df
        except Exception:
            pass

    ticker_yf = f"{ativo}.SA"
    print(f"  Baixando OHLCV {ativo} ({ano_ini}→{ano_fim})...")
    try:
        raw = yf.Ticker(ticker_yf).history(
            start=f"{ano_ini}-01-01",
            end=f"{ano_fim}-12-31",
            auto_adjust=True)
        if raw.empty:
            print(f"  ⚠ Sem dados para {ativo}")
            return pd.DataFrame()
        raw.index = pd.to_datetime(raw.index).tz_localize(None)
        df = raw[["Open","High","Low","Close","Volume"]].copy()
        df.columns = ["open","high","low","close","volume"]
        df = df[df["close"] > 0].dropna()
        lr = np.log(df["close"]/df["close"].shift(1))
        df["vol_21d"]       = lr.rolling(21).std()*math.sqrt(252)
        df["vol_63d"]       = lr.rolling(63).std()*math.sqrt(252)
        df["vol_garch_21d"] = lr.ewm(
            span=21,adjust=False).std()*math.sqrt(252)
        df = df.dropna()
        df.to_parquet(cache_path)
        mb = os.path.getsize(cache_path)/1e6
        print(f"  ✓ OHLCV {ativo}: {len(df):,} dias | {mb:.2f} MB")
        return df
    except Exception as e:
        print(f"  ✗ Falha OHLCV {ativo}: {e}")
        return pd.DataFrame()


def tape_ibov_carregar(anos: list) -> pd.Series:
    cache_path = os.path.join(OHLCV_DIR, "IBOV.parquet")
    ano_ini    = min(anos) - 2
    ano_fim    = max(anos)

    if os.path.exists(cache_path):
        try:
            df = pd.read_parquet(cache_path)
            if "data" in df.columns:
                df = df.set_index("data")
            df.index = pd.to_datetime(df.index)
            if (df.index.year.min() <= ano_ini and
                    df.index.year.max() >= ano_fim):
                print(f"  ✓ IBOV cache: {len(df):,} dias")
                return df["close"]
        except Exception:
            pass

    print(f"  Baixando IBOV ({ano_ini}→{ano_fim})...")
    try:
        raw = yf.Ticker(TICKER_IBOV).history(
            start=f"{ano_ini}-01-01",
            end=f"{ano_fim}-12-31",
            auto_adjust=True)
        raw.index = pd.to_datetime(raw.index).tz_localize(None)
        s = raw["Close"]
        s.to_frame(name="close").to_parquet(cache_path)
        print(f"  ✓ IBOV: {len(s):,} dias")
        return s
    except Exception as e:
        print(f"  ⚠ Falha IBOV: {e}")
        return pd.Series(dtype=float)


def tape_externa_carregar(nome: str, anos: list) -> pd.Series:
    mapa = {"usdbrl": "USDBRL=X", "minerio": "TIO=F"}
    if nome not in mapa:
        print(f"  ⚠ Série externa desconhecida: {nome}")
        return None

    ticker     = mapa[nome]
    cache_path = os.path.join(EXTERNAS_DIR, f"{nome}.parquet")
    ano_ini    = min(anos) - 2
    ano_fim    = max(anos)

    if os.path.exists(cache_path):
        try:
            df = pd.read_parquet(cache_path)
            if "data" in df.columns:
                df = df.set_index("data")
            df.index = pd.to_datetime(df.index)
            if (df.index.year.min() <= ano_ini and
                    df.index.year.max() >= ano_fim):
                print(f"  ✓ Cache externa {nome}: {len(df):,} dias")
                return (df["close"] if "close" in df.columns
                        else df.iloc[:, 0])
        except Exception:
            pass

    print(f"  Baixando série externa {nome} ({ticker}) "
          f"{ano_ini}→{ano_fim}...")
    try:
        raw = yf.Ticker(ticker).history(
            start=f"{ano_ini}-01-01",
            end=f"{ano_fim}-12-31",
            auto_adjust=True)
        if raw.empty:
            print(f"  ⚠ Sem dados para {nome}")
            return None
        raw.index = pd.to_datetime(raw.index).tz_localize(None)
        serie = (raw["Close"] if "Close" in raw.columns
                 else raw.iloc[:, 0])
        serie.to_frame(name="close").to_parquet(cache_path)
        mb = os.path.getsize(cache_path)/1e6
        print(f"  ✓ Série externa {nome}: {len(serie):,} dias "
              f"| {mb:.2f} MB")
        return serie
    except Exception as e:
        print(f"  ✗ Falha ao baixar {nome}: {e}")
        return None


# ════════════════════════════════════════════════════════════════════
# SÉRIES EXTERNAS — função de alto nível para carregar todas as ativas
# ════════════════════════════════════════════════════════════════════

def tape_externas_carregar(ativos: list, anos: list) -> dict:
    """
    Identifica séries externas ativas na configuração dos ativos,
    baixa e cacheia via tape_externa_carregar().

    Retorna dict {nome_serie: pd.Series} com todas as séries ativas.
    Segue o mesmo padrão de tape_ohlcv_carregar() e tape_ibov_carregar() —
    o chamador recebe dados prontos sem saber como foram obtidos.

    Extensibilidade: adicionar nova fonte = novo entry no mapa
    dentro de tape_externa_carregar() — tape_externas_carregar() não muda.
    """
    series_ativas = set()

    for ticker in ativos:
        cfg = tape_ativo_carregar(ticker)
        for nome_serie, ativa in cfg.get("externas", {}).items():
            if ativa:
                series_ativas.add(nome_serie)

    externas = {}
    for nome_serie in sorted(series_ativas):
        serie = tape_externa_carregar(nome_serie, anos)
        if serie is not None:
            externas[nome_serie] = serie
            print(f"  ✓ Série externa {nome_serie}: {len(serie):,} dias")
        else:
            print(f"  ~ Série externa {nome_serie}: indisponível")

    return externas


# ════════════════════════════════════════════════════════════════════
# SELIC
# ════════════════════════════════════════════════════════════════════

def _obter_selic(ano_ini, ano_fim):
    df_cache = pd.DataFrame()
    if os.path.exists(SELIC_CACHE):
        try:
            df_cache = pd.read_parquet(SELIC_CACHE)
            df_cache["data"] = pd.to_datetime(df_cache["data"])
            ano_min = df_cache["data"].dt.year.min()
            ano_max = df_cache["data"].dt.year.max()
            if ano_min <= ano_ini and ano_max >= ano_fim:
                df = df_cache[
                    (df_cache["data"].dt.year >= ano_ini) &
                    (df_cache["data"].dt.year <= ano_fim)
                ].copy()
                print(f"  ✓ SELIC cache: {len(df):,} dias "
                      f"({ano_ini}→{ano_fim})")
                return df
        except Exception:
            df_cache = pd.DataFrame()

    ano_bcb_ini = min(ano_ini, 2000)
    ano_bcb_fim = max(ano_fim, date.today().year)
    url = (f"{BCB_SELIC_URL}?formato=json"
           f"&dataInicial=01/01/{ano_bcb_ini}"
           f"&dataFinal=31/12/{ano_bcb_fim}")

    print(f"  Obtendo SELIC BCB ({ano_bcb_ini}→{ano_bcb_fim})...")
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "python-requests/2.28.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            dados = json.loads(r.read().decode())

        df_novo = pd.DataFrame(dados)
        df_novo["data"]     = pd.to_datetime(
            df_novo["data"], format="%d/%m/%Y")
        df_novo["selic_ad"] = pd.to_numeric(
            df_novo["valor"], errors="coerce") / 100
        df_novo["selic_aa"] = (
            (1 + df_novo["selic_ad"])**252 - 1) * 100
        df_novo = (df_novo[["data","selic_aa"]]
                   .dropna()
                   .sort_values("data")
                   .reset_index(drop=True))

        if not df_cache.empty:
            df_total = (pd.concat([df_cache, df_novo],
                                  ignore_index=True)
                        .drop_duplicates(subset=["data"])
                        .sort_values("data")
                        .reset_index(drop=True))
        else:
            df_total = df_novo

        df_total.to_parquet(SELIC_CACHE, index=False)
        print(f"  ✓ SELIC: {len(df_total):,} dias")
        return df_total[
            (df_total["data"].dt.year >= ano_ini) &
            (df_total["data"].dt.year <= ano_fim)
        ].copy()

    except Exception as e:
        print(f"  ⚠ BCB indisponível ({e}) — fallback diário")
        rows = []
        for ano, selic_aa in SELIC_HISTORICA.items():
            if ano_bcb_ini <= ano <= ano_bcb_fim:
                for d in pd.date_range(
                        f"{ano}-01-01",
                        f"{ano}-12-31", freq="B"):
                    rows.append({"data": d, "selic_aa": selic_aa})
        df_fb = (pd.DataFrame(rows)
                 .sort_values("data")
                 .reset_index(drop=True))
        df_fb.to_parquet(SELIC_CACHE, index=False)
        print(f"  ✓ SELIC fallback: {len(df_fb):,} dias úteis")
        return df_fb[
            (df_fb["data"].dt.year >= ano_ini) &
            (df_fb["data"].dt.year <= ano_fim)
        ].copy()


def _selic_array(datas, df_selic):
    if df_selic is None or df_selic.empty:
        return np.array([math.log(1 + SELIC_HISTORICA.get(
            pd.Timestamp(d).year, 13.5)/100) for d in datas])
    idx = pd.to_datetime(df_selic["data"])
    result = []
    for d in datas:
        mask = idx <= pd.Timestamp(d)
        s = (float(df_selic.loc[mask,"selic_aa"].iloc[-1])/100
             if mask.any()
             else SELIC_HISTORICA.get(
                 pd.Timestamp(d).year, 13.5)/100)
        result.append(math.log(1+s))
    return np.array(result)


# ════════════════════════════════════════════════════════════════════
# BLACK-SCHOLES VETORIZADO
# ════════════════════════════════════════════════════════════════════

def _calcular_iv_lote(pm, S, K, T, r, tipos):
    S,K,T,r,pm = (np.asarray(x,dtype=float)
                  for x in [S,K,T,r,pm])
    ic     = np.array([t=="CALL" for t in tipos], dtype=bool)
    n      = len(pm)
    sigmas = np.linspace(0.01, 4.0, 200)
    ivs    = np.full(n, np.nan)
    for ini in range(0, n, LOTE_IV):
        fim  = min(ini+LOTE_IV, n)
        m    = fim - ini
        sl   = slice(ini, fim)
        S_b  = S[sl][:,None];  K_b  = K[sl][:,None]
        T_b  = T[sl][:,None];  r_b  = r[sl][:,None]
        pm_b = pm[sl];         ic_b = ic[sl]
        sg_b = sigmas[None,:]
        v    = (T_b>0)&(sg_b>0)&(S_b>0)&(K_b>0)
        S_   = np.where(v,S_b,1.);  K_  = np.where(v,K_b,1.)
        T_   = np.where(v,T_b,1.);  sg_ = np.where(v,sg_b,0.3)
        r_   = np.broadcast_to(r_b,(m,len(sigmas)))
        d1   = (np.log(S_/K_)+(r_+0.5*sg_**2)*T_)/(sg_*np.sqrt(T_))
        d2   = d1 - sg_*np.sqrt(T_)
        bs   = np.where(ic_b[:,None],
                   S_*_norm.cdf(d1)-K_*np.exp(-r_*T_)*_norm.cdf(d2),
                   K_*np.exp(-r_*T_)*_norm.cdf(-d2)-S_*_norm.cdf(-d1))
        diff  = bs - pm_b[:,None]
        cross = np.diff(np.sign(diff), axis=1)
        for j in np.where(np.any(cross!=0,axis=1))[0]:
            idx_c = np.where(cross[j]!=0)[0]
            if not len(idx_c): continue
            i0      = idx_c[0]
            s0, s1  = sigmas[i0], sigmas[i0+1]
            d0, d1_ = diff[j,i0], diff[j,i0+1]
            dn      = d1_ - d0
            if abs(dn) < 1e-10: continue
            iv = s0 - d0*(s1-s0)/dn
            if 0.01 <= iv <= 5.0:
                ivs[ini+j] = round(float(iv), 4)
    return ivs


def _gregas_vetorizadas(S, K, T, r, sigma, tipos):
    S,K,T,r,sg = (np.asarray(x,dtype=float)
                  for x in [S,K,T,r,sigma])
    ic  = np.array([t=="CALL" for t in tipos], dtype=bool)
    v   = (T>0)&(sg>0)&(S>0)&(K>0)
    S_  = np.where(v,S,1.);  K_  = np.where(v,K,1.)
    T_  = np.where(v,T,1.);  sg_ = np.where(v,sg,0.3)
    d1  = (np.log(S_/K_)+(r+0.5*sg_**2)*T_)/(sg_*np.sqrt(T_))
    d2  = d1 - sg_*np.sqrt(T_)
    nd1 = _norm.pdf(d1)
    delta = np.where(ic, _norm.cdf(d1), _norm.cdf(d1)-1.0)
    gamma = np.where(v, nd1/(S_*sg_*np.sqrt(T_)), np.nan)
    th_c  = (-(S_*nd1*sg_)/(2*np.sqrt(T_)) -
             r*K_*np.exp(-r*T_)*_norm.cdf(d2)) / 252
    th_p  = (-(S_*nd1*sg_)/(2*np.sqrt(T_)) +
             r*K_*np.exp(-r*T_)*_norm.cdf(-d2)) / 252
    return {
        "delta": np.where(v, delta,                  np.nan),
        "gamma": np.where(v, gamma,                  np.nan),
        "theta": np.where(v, np.where(ic,th_c,th_p), np.nan),
        "vega":  np.where(v, S_*nd1*np.sqrt(T_)/100, np.nan),
    }


# ════════════════════════════════════════════════════════════════════
# COTAHIST
# ════════════════════════════════════════════════════════════════════

def _cache_ok(path, min_mb):
    if not os.path.exists(path):
        return False
    try:
        mb = os.path.getsize(path) / 1e6
    except OSError:
        return False
    if min_mb > 0 and mb < min_mb:
        print(f"  ⚠ Cache suspeito: {os.path.basename(path)} "
              f"({mb:.1f}MB < {min_mb}MB) — recalculando")
        return False
    if mb == 0:
        print(f"  ⚠ Cache vazio: {os.path.basename(path)} — recalculando")
        return False
    return True

def _cache_valido(path_parquet, min_linhas=50):
    """
    Verifica se o cache parquet é válido.
    Retorna True se válido, False se deve recalcular.
    """
    try:
        df = pd.read_parquet(path_parquet)

        # Verifica estrutura mínima
        colunas_obrigatorias = [
            "data", "ticker", "tipo", "strike",
            "fechamento", "delta", "iv", "T"
        ]
        if not all(c in df.columns for c in colunas_obrigatorias):
            print(f"  ⚠ Cache suspeito: colunas faltando — recalculando")
            return False

        # Verifica volume mínimo de dados
        if len(df) < min_linhas:
            print(f"  ⚠ Cache suspeito: {len(df)} linhas < {min_linhas} — recalculando")
            return False

        return True

    except Exception as e:
        print(f"  ⚠ Cache corrompido: {e} — recalculando")
        return False


def _cache_path(ativo, ano):
    return os.path.join(GREGAS_DIR, f"{ativo}_{ano}.parquet")

def _parse_preco(s):
    s = s.strip()
    return 0.0 if not s or s == "0"*len(s) else int(s)/100.0

def _parse_preco_eod(s):
    """Converte strike do formato EOD: '7896' → 78.96"""
    try:
        return float(str(s).strip()) / 100.0
    except (ValueError, TypeError):
        return 0.0

def _parse_data(s):
    s = s.strip()
    if len(s) != 8 or s == "00000000": return None
    try: return datetime.strptime(s, "%Y%m%d").date()
    except: return None

def _detectar_ativo_base(codneg, ativos):
    cod = codneg.strip().upper()
    for ativo in ativos:
        base = ativo.replace(".SA","").upper()
        if cod == base or cod.startswith(base[:4]):
            return base
    if cod[:4] == "BVMF" and any("BOVA11" in a for a in ativos):
        return "BOVA11"
    return None

# DELTA CHAOS — TAPE patch — _baixar_cotahist com suporte a mensais
# Substitui a função _baixar_cotahist integralmente

def _baixar_cotahist(ano, forcar=False):
    from datetime import date as _date

    txt_anual = os.path.join(COTAHIST_DIR, f"COTAHIST_A{ano}.TXT")
    _min_mb   = (carregar_config()["tape"]["min_cotahist_mb_antigo"]
                 if ano < carregar_config()["tape"]["ano_corte_cotahist"]
                 else MIN_COTAHIST_MB)

    # ── Anual em cache válido ─────────────────────────────────────
    if not forcar and _cache_ok(txt_anual, _min_mb):
        print(f"  Cache COTAHIST {ano}: "
              f"{os.path.getsize(txt_anual)/1e6:.0f} MB")
        return [txt_anual]

    # ── Tenta baixar o anual ──────────────────────────────────────
    url_anual = f"{COTAHIST_URL}/COTAHIST_A{ano}.ZIP"
    try:
        with urllib.request.urlopen(
            urllib.request.Request(
                url_anual,
                headers={"User-Agent": "Mozilla/5.0"}),
            timeout=30) as resp:
            chunks = []
            while True:
                chunk = resp.read(262144)
                if not chunk: break
                chunks.append(chunk)

        with zipfile.ZipFile(
                io.BytesIO(b"".join(chunks))) as z:
            txts = [n for n in z.namelist()
                    if n.upper().endswith(".TXT")]
            if txts:
                z.extract(txts[0], COTAHIST_DIR)
                ext = os.path.join(COTAHIST_DIR, txts[0])
                if ext != txt_anual:
                    if os.path.exists(txt_anual):
                        os.remove(txt_anual)
                    os.rename(ext, txt_anual)
                if _cache_ok(txt_anual, _min_mb):
                    print(f"  ✓ COTAHIST {ano}: "
                          f"{os.path.getsize(txt_anual)/1e6:.0f} MB")
                    return [txt_anual]

    except Exception:
        pass  # anual indisponível — tenta mensais abaixo

    # ── Anual indisponível — mensais apenas para ano corrente ─────
    ano_atual = _date.today().year
    mes_atual = _date.today().month

    if ano != ano_atual:
        print(f"  ✗ COTAHIST {ano}: anual indisponível "
              f"e não é ano corrente — pulando")
        return []

    print(f"  COTAHIST {ano}: anual indisponível "
          f"— baixando mensais 01 a {mes_atual:02d}...")
    txts_mensais = []

    for mes in range(1, mes_atual + 1):
        nome     = f"COTAHIST_M{mes:02d}{ano}"
        txt_path = os.path.join(COTAHIST_DIR, f"{nome}.TXT")

        if not forcar and _cache_ok(txt_path, 1.0):
            print(f"  Cache COTAHIST {ano}-{mes:02d}: "
                  f"{os.path.getsize(txt_path)/1e6:.0f} MB")
            txts_mensais.append(txt_path)
            continue

        url = f"{COTAHIST_URL}/{nome}.ZIP"
        try:
            with urllib.request.urlopen(
                urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"}),
                timeout=120) as resp:
                chunks = []
                total  = int(resp.headers.get(
                    "Content-Length", 0))
                with _tqdm(
                        total=total if total > 0 else None,
                        unit="B", unit_scale=True,
                        unit_divisor=1024,
                        desc=f"COTAHIST_{ano}-{mes:02d}",
                        ncols=None) as pbar:
                    while True:
                        chunk = resp.read(262144)
                        if not chunk: break
                        chunks.append(chunk)
                        pbar.update(len(chunk))

            with zipfile.ZipFile(
                    io.BytesIO(b"".join(chunks))) as z:
                txts = [n for n in z.namelist()
                        if n.upper().endswith(".TXT")]
                if not txts:
                    print(f"  ⚠ COTAHIST {ano}-{mes:02d}: "
                          f"ZIP sem TXT — pulando")
                    continue
                z.extract(txts[0], COTAHIST_DIR)
                ext = os.path.join(COTAHIST_DIR, txts[0])
                if ext != txt_path:
                    if os.path.exists(txt_path):
                        os.remove(txt_path)
                    os.rename(ext, txt_path)

            mb = os.path.getsize(txt_path) / 1e6
            print(f"  ✓ COTAHIST {ano}-{mes:02d}: {mb:.0f} MB")
            txts_mensais.append(txt_path)

        except Exception as e:
            print(f"  ✗ COTAHIST {ano}-{mes:02d}: {e} — pulando")

    return txts_mensais

def _ler_cotahist(txt_path, ativos, anos=None):
    registros = []
    with open(txt_path, "r", encoding="latin-1") as f:
        for linha in f:
            if len(linha)<245 or linha[0:2]!="01": continue
            tpmerc = linha[24:27]
            if tpmerc not in (TPMERC_ACAO,
                              TPMERC_CALL,
                              TPMERC_PUT): continue
            data = _parse_data(linha[2:10])
            if not data or (anos and
                            data.year not in anos): continue
            codneg = linha[12:24].strip()
            ab     = _detectar_ativo_base(codneg, ativos)
            if not ab: continue
            tipo = ("ACAO" if tpmerc==TPMERC_ACAO
                    else "CALL" if tpmerc==TPMERC_CALL
                    else "PUT")
            eh_opcao = tpmerc != TPMERC_ACAO
            registros.append({
                "data":         data,
                "ativo_base":   ab,
                "ticker":       codneg,
                "tipo":         tipo,
                "abertura":     _parse_preco(linha[56:69]),
                "fechamento":   _parse_preco(linha[69:82]),
                "minimo":       _parse_preco(linha[95:108]),
                "maximo":       _parse_preco(linha[108:121]),
                "n_negocios":   int(linha[147:152].strip() or 0),
                "volume":       _parse_preco(linha[170:188]),
                "strike":       (_parse_preco(linha[188:201])
                                 if eh_opcao else None),
                "vencimento":   (_parse_data(linha[202:210])
                                 if eh_opcao else None),
                # open_interest adicionado — necessário para GEX/REFLECT
                "open_interest": (int(linha[210:223].strip() or 0)
                                  if eh_opcao else None),
            })
    if not registros: return pd.DataFrame()
    df = pd.DataFrame(registros)
    df["data"]       = pd.to_datetime(df["data"])
    df["vencimento"] = pd.to_datetime(df["vencimento"])
    return df[df["fechamento"] > 0]

def _enriquecer(df, df_selic):
    df_ac  = df[df["tipo"]=="ACAO"][
        ["data","ativo_base","fechamento"]].copy()
    df_ac  = df_ac.rename(columns={"fechamento":"preco_acao"})
    df_op  = df[df["tipo"].isin(["CALL","PUT"])].copy()
    if df_op.empty or df_ac.empty:
        return pd.DataFrame()
    df_enr = df_op.merge(
        df_ac, on=["data","ativo_base"], how="left")
    df_enr = df_enr.dropna(
        subset=["preco_acao","strike","vencimento"])
    df_enr = df_enr[
        (df_enr["preco_acao"]>0) &
        (df_enr["strike"]>0) &
        (df_enr["fechamento"]>0)]
    df_enr["T"] = (
        pd.to_datetime(df_enr["vencimento"]) -
        pd.to_datetime(df_enr["data"])
    ).dt.days / 365.0
    df_enr = df_enr[df_enr["T"]>0].reset_index(drop=True)
    if df_enr.empty: return pd.DataFrame()
    n = len(df_enr)
    print(f"    {n:,} opções — calculando IV e gregas...")
    r_arr = _selic_array(df_enr["data"].values, df_selic)
    S     = df_enr["preco_acao"].values
    K     = df_enr["strike"].values
    T     = df_enr["T"].values
    pm    = df_enr["fechamento"].values
    tipos = df_enr["tipo"].tolist()
    ivs   = np.full(n, np.nan)
    with _tqdm(total=n, desc="    IV",
               unit="opts", ncols=None) as pbar:
        for ini in range(0, n, LOTE_IV):
            fim     = min(ini+LOTE_IV, n)
            sl      = slice(ini, fim)
            ivs[sl] = _calcular_iv_lote(
                pm[sl],S[sl],K[sl],
                T[sl],r_arr[sl],tipos[ini:fim])
            pbar.update(fim-ini)
    sigma = np.where(np.isfinite(ivs), ivs, 0.30)
    g     = _gregas_vetorizadas(S, K, T, r_arr, sigma, tipos)
    df_enr["iv"]              = np.round(ivs,        4)
    df_enr["delta"]           = np.round(g["delta"], 4)
    df_enr["gamma"]           = np.round(g["gamma"], 6)
    df_enr["theta"]           = np.round(g["theta"], 4)
    df_enr["vega"]            = np.round(g["vega"],  4)
    df_enr["selic"]           = np.round(r_arr*100,  4)
    df_enr["r"]               = np.round(r_arr,      6)
    df_enr["dist_strike"]     = np.round((K/S-1)*100, 2)
    df_enr["volume_medio_5d"] = (
        df_enr.sort_values(["ativo_base","ticker","data"])
        .groupby(["ativo_base","ticker"])["volume"]
        .transform(lambda x: x.rolling(5, min_periods=1).mean()))
    df_enr["iv_rank"]         = np.nan
    df_enr["schema_version"]  = SCHEMA_VERSION
    df_enr["fonte"]           = "backtest"
    pct = np.isfinite(ivs).mean() * 100
    print(f"    ✓ IV convergiu em {pct:.1f}% | "
          f"delta médio: {df_enr['delta'].mean():.4f}")
    return df_enr


# ════════════════════════════════════════════════════════════════════
# REFLECT — funções auxiliares privadas
# ════════════════════════════════════════════════════════════════════

def _calcular_zscore_rolling(series: pd.Series,
                              window: int) -> pd.Series:
    """
    Z-score rolling.
    SCAN-1: min_periods = max(3, window//2) para evitar z-scores
    instáveis com 1-2 amostras nos primeiros ciclos.
    Retorna 0.0 onde não há dados suficientes — sinalizado no log.
    """
    if series.empty:
        return pd.Series(dtype=float)

    min_p = max(3, window // 2)
    rolling_mean = series.rolling(window=window,
                                  min_periods=min_p).mean()
    rolling_std  = series.rolling(window=window,
                                  min_periods=min_p).std()
    rolling_std  = rolling_std.replace(0, np.nan)
    z = (series - rolling_mean) / rolling_std
    n_nan = z.isna().sum()
    if n_nan > 0:
        pass  # ciclos iniciais sem dados suficientes — normal
    return z.fillna(0.0)


def _get_vencimento_referencia(df_options: pd.DataFrame):
    """Retorna o vencimento com maior open interest total."""
    if df_options.empty:
        return None
    venc_oi = df_options.groupby("vencimento")["open_interest"].sum()
    if venc_oi.empty:
        return None
    return venc_oi.idxmax()


def _calculate_gex(df_options_filtered: pd.DataFrame,
                   preco_acao: float) -> float:
    """
    Gamma Exposure (dado auxiliar de diagnóstico).
    Não entra na fórmula do score — armazenado no daily_history
    para análise futura.
    Convenção: calls positivo, puts negativo (perspectiva do dealer).
    """
    if df_options_filtered.empty or preco_acao <= 0:
        return 0.0
    gex = (df_options_filtered["gamma"] *
           df_options_filtered["open_interest"] *
           df_options_filtered["strike"]**2 *
           np.where(df_options_filtered["tipo"] == "PUT", -1, 1))
    return float(gex.sum() / 1_000_000)


def _process_eod_options_data(df_eod_raw: pd.DataFrame,
                               ativo_base: str,
                               data: str) -> pd.DataFrame:
    """
    Filtra e prepara dados do arquivo EOD para o REFLECT.
    Aplica: conversão de strikes, filtro NaN, filtro 20% ATM.
    """
    column_map = {
        "ticker":        "ticker",
        "vencimento":    "vencimento",
        "strike":        "strike",
        "tipo":          "tipo",
        "fechamento":    "fechamento",
        "open_interest": "open_interest",
        "delta":         "delta",
        "gamma":         "gamma",
        "iv":            "iv",
    }
    df = df_eod_raw.rename(
        columns={k: v for k, v in column_map.items()
                 if k in df_eod_raw.columns})

    # Normaliza tipo: C/P → CALL/PUT
    if "tipo" in df.columns:
        df["tipo"] = (df["tipo"].astype(str).str.upper()
                      .replace({"C": "CALL", "P": "PUT"}))

    # Converte strikes: 7896 → 78.96
    if "strike" in df.columns:
        df["strike"] = df["strike"].apply(_parse_preco_eod)

    if "vencimento" in df.columns:
        df["vencimento"] = pd.to_datetime(
            df["vencimento"], dayfirst=True, errors="coerce")

    df["data"]       = pd.to_datetime(data)
    df["ativo_base"] = ativo_base
    df["T"] = ((df["vencimento"] - df["data"]).dt.days / 365.0
               if "vencimento" in df.columns else np.nan)

    # Preço da ação do dia via OHLCV cache
    current_year = pd.to_datetime(data).year
    df_ohlcv = tape_ohlcv_carregar(ativo_base, [current_year - 1, current_year])
    data_ts  = pd.to_datetime(data)
    preco_acao = None
    if not df_ohlcv.empty:
        subset = df_ohlcv.loc[df_ohlcv.index <= data_ts, "close"]
        if not subset.empty:
            preco_acao = float(subset.iloc[-1])

    if preco_acao is None or preco_acao <= 0:
        print(f"  ⚠ Sem preco_acao para {ativo_base} em {data} "
              f"— EOD ignorado")
        return pd.DataFrame()

    # Filtros de qualidade mínima
    required = ["strike", "fechamento", "T",
                "delta", "gamma", "iv", "open_interest"]
    for col in required:
        if col not in df.columns:
            return pd.DataFrame()

    df_f = df[
        df["strike"].notna() & (df["strike"] > 0) &
        df["fechamento"].notna() & (df["fechamento"] > 0) &
        df["T"].notna() & (df["T"] > 0) &
        df["delta"].notna() &
        df["gamma"].notna() &
        df["iv"].notna() &
        df["open_interest"].notna() &
        (df["open_interest"] > 0)
    ].copy()

    # Filtro 20% ATM
    atm_pct = carregar_config()["reflect"]["gex_atm_distance_pct_filter"]
    df_f["dist_atm_pct"] = (df_f["strike"] / preco_acao - 1).abs() * 100
    df_f = df_f[df_f["dist_atm_pct"] <= atm_pct].copy()
    df_f["preco_acao"] = preco_acao

    return df_f


def _calculate_divergence_components(
        df_options: pd.DataFrame,
        ativo_base: str,
        data: str) -> dict:
    """
    Calcula os dois ratios de divergência bidirecional.

    Ratio 1 (iv_prem_ratio):
      IV implícita ponderada por OI / prêmio médio ponderado por OI.
      Sobe quando o mercado precifica mais risco do que o sistema captura.

    Ratio 2 (ret_vol_ratio):
      Retorno diário realizado / (IV_anualizada / sqrt(252)).
      Sobe quando o ativo se move mais do que a IV previa —
      o sistema está vendendo vol estruturalmente barata.

    SCAN-3: proteção explícita contra divisão por zero em ret_vol_ratio.
    """
    if df_options.empty:
        return {"iv_prem_ratio": np.nan, "ret_vol_ratio": np.nan}

    venc_ref = _get_vencimento_referencia(df_options)
    if venc_ref is None:
        return {"iv_prem_ratio": np.nan, "ret_vol_ratio": np.nan}

    df_ref = df_options[
        df_options["vencimento"] == venc_ref].copy()
    if df_ref.empty:
        return {"iv_prem_ratio": np.nan, "ret_vol_ratio": np.nan}

    total_oi = df_ref["open_interest"].sum()
    if total_oi <= 0:
        return {"iv_prem_ratio": np.nan, "ret_vol_ratio": np.nan}

    iv_pond     = float((df_ref["iv"] *
                         df_ref["open_interest"]).sum() / total_oi)
    premio_pond = float((df_ref["fechamento"] *
                         df_ref["open_interest"]).sum() / total_oi)

    # Ratio 1
    iv_prem_ratio = (iv_pond / (premio_pond + 1e-10)
                     if premio_pond > 0 else np.nan)

    # Ratio 2
    current_year = pd.to_datetime(data).year
    df_ohlcv     = tape_ohlcv_carregar(ativo_base,
                               [current_year - 1, current_year])
    ret_vol_ratio = np.nan
    if not df_ohlcv.empty and iv_pond > 0:
        data_ts = pd.to_datetime(data)
        subset  = df_ohlcv.loc[df_ohlcv.index <= data_ts, "close"]
        if len(subset) >= 2:
            preco_hoje     = float(subset.iloc[-1])
            preco_anterior = float(subset.iloc[-2])
            if preco_anterior > 0:
                retorno_diario = preco_hoje / preco_anterior - 1.0
                # SCAN-3: proteção divisão por zero
                iv_diaria = iv_pond / math.sqrt(252)
                if iv_diaria > 1e-8:
                    ret_vol_ratio = retorno_diario / iv_diaria

    return {"iv_prem_ratio": iv_prem_ratio,
            "ret_vol_ratio": ret_vol_ratio}


# ════════════════════════════════════════════════════════════════════
# REFLECT — interface pública
# ════════════════════════════════════════════════════════════════════


    # Extrai data do nome do arquivo (formato: ..._YYYY-MM-DD.xlsx)
    basename  = os.path.basename(filepath)
    data_part = basename.split("_")[-1].split(".")[0]
    try:
        data_ref = pd.to_datetime(
            data_part, format="%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        data_ref = date.today().strftime("%Y-%m-%d")

    # Inferência de ativo base
    if "ativo_base" not in df_raw.columns:
        if "ticker" not in df_raw.columns:
            print("  ⚠ Coluna 'ticker' não encontrada no EOD")
            return
        # SCAN-7 (limitação conhecida): funciona para ativos de 4 chars
        # Registrar quando universo expandir para ativos de 5 chars
        unique_bases = df_raw["ticker"].astype(str).str[:4].unique()
        if len(unique_bases) == 1:
            df_raw["ativo_base"] = unique_bases[0]
        else:
            print("  ⚠ Múltiplos ativos base no EOD — "
                  "adicione coluna 'ativo_base'")
            return


# ════════════════════════════════════════════════════════════════════
# INTERFACE PÚBLICA
# ════════════════════════════════════════════════════════════════════

def tape_historico_carregar(ativos, anos, forcar=False):
    ativos = [a.replace(".SA","").upper() for a in ativos]
    print(f"\n{'═'*60}")
    print(f"  TAPE.backtest")
    print(f"  Ativos:  {ativos}")
    print(f"  Anos:    {anos}")
    print(f"  Cache:   {TAPE_DIR}")
    print(f"{'═'*60}")
    df_selic = _obter_selic(min(anos), max(anos))
    frames   = []
    total    = len(anos) * len(ativos)
    with _tqdm(total=total, desc="Progresso",
               unit="job", ncols=None) as pbar:
        for ano in anos:
            txts = _baixar_cotahist(ano, forcar=forcar)
            if not txts:
                pbar.update(len(ativos)); continue

            for txt in txts:                     # anual = 1 item, mensais = N itens
                for ativo in ativos:
                    pbar.set_description(f"{ativo} {ano}")
                    cache = _cache_path(ativo, ano)

                    _min_gregas = (
                        carregar_config()["tape"]
                        ["min_gregas_mb_antigo"]
                        if ano < carregar_config()["tape"]
                        ["ano_corte_gregas"]
                        else MIN_GREGAS_MB)

                    if not forcar and _cache_ok(
                            cache, _min_gregas):
                        mb = os.path.getsize(cache) / 1e6
                        print(f"\n  ✓ {ativo} {ano} "
                              f"cache ({mb:.1f} MB)")
                        try:
                            frames.append(
                                pd.read_parquet(cache))
                        except Exception as e:
                            print(f"\n  ⚠ {ativo} {ano} "
                                  f"cache corrompido: {e} "
                                  f"— reprocessando")
                            os.remove(cache)
                        else:
                            pbar.update(1)
                            continue

                    try:
                        df_raw = _ler_cotahist(
                            txt, [ativo], [ano])
                    except Exception as e:
                        print(f"\n  ⚠ {ativo} {ano} "
                              f"erro COTAHIST: {e} — pulando")
                        pbar.update(1)
                        continue

                    if df_raw.empty:
                        print(f"\n  ~ {ativo} {ano}: "
                              f"sem dados — pulando")
                        pbar.update(1)
                        continue

                    n_op = (df_raw["tipo"].isin(
                        ["CALL","PUT"])).sum()
                    if n_op == 0:
                        print(f"\n  ~ {ativo} {ano}: "
                              f"sem opções — pulando")
                        pbar.update(1)
                        continue

                    print(f"\n  {ativo} {ano}: "
                          f"{n_op:,} opções")

                    try:
                        df_enr = _enriquecer(
                            df_raw, df_selic)
                    except Exception as e:
                        print(f"\n  ⚠ {ativo} {ano} "
                              f"erro enriquecimento: {e} "
                              f"— pulando")
                        pbar.update(1)
                        continue

                    if df_enr.empty:
                        print(f"\n  ~ {ativo} {ano}: "
                              f"enriquecimento vazio — pulando")
                        pbar.update(1)
                        continue

                    try:
                        df_enr.to_parquet(
                            cache, index=False)
                        print(f"  ✓ Salvo: "
                              f"{os.path.basename(cache)} "
                              f"({os.path.getsize(cache)/1e6:.1f} MB)")
                    except Exception as e:
                        print(f"  ⚠ Falha cache {ativo} "
                              f"{ano}: {e}")

                    frames.append(df_enr)
                    pbar.update(1)

    if not frames:
        print("  ✗ Nenhum dado.")
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    print(f"\n  ✓ Concluído: {len(df):,} registros")
    return df

def tape_eod_carregar(ativo, filepath, preco_acao=None, data=None):
    ativo = ativo.replace(".SA","").upper()
    data  = data or str(date.today())
    print(f"  TAPE.paper: {ativo} — {filepath}")

    try:
        df_raw = pd.read_excel(filepath, header=1)
    except Exception as e:
        try:
            df_raw = pd.read_csv(
                filepath, sep=";",
                encoding="latin-1", header=1)
        except Exception as e2:
            print(f"  ✗ {e2}")
            return pd.DataFrame()

    # Normaliza nomes — remove \xa0, espaços, caracteres especiais
    df_raw.columns = [
        str(c).strip()
        .replace("\xa0","")
        .replace(" ","_")
        .replace(".","")
        .replace("(","").replace(")","")
        .replace("/","_")
        .replace("%","pct")
        .replace("$","")
        .lower()
        for c in df_raw.columns
    ]

    # Remove linhas sem ticker
    df_raw = df_raw[df_raw.iloc[:,0].notna()].copy()
    df_raw = df_raw[
        df_raw.iloc[:,0].astype(str).str.len() >= 5
    ].copy()

    # Mapeamento exato para formato opcoes.net.br
    mapa = {
        "ticker":           "ticker",
        "vencimento":       "vencimento",
        "dias_úteis":       "dias_uteis",
        "dias_uteis":       "dias_uteis",
        "tipo":             "tipo",
        "strike":           "strike",
        "a_i_otm":          "moneyness",
        "dist__pct_do_strike": "dist_strike",
        "último":           "fechamento",
        "ultimo":           "fechamento",
        "delta":            "delta",
        "gamma":            "gamma",
        "theta_":           "theta",
        "vega":             "vega",
        "vol_financeiro":   "volume",
        "lanç":             "lancamentos",
        "tit":              "open_interest",
        "núm_de_neg":       "n_negocios",
        "num_de_neg":       "n_negocios",
    }

    df_raw = df_raw.rename(columns={
        k: v for k, v in mapa.items()
        if k in df_raw.columns
    })

    # Garante coluna ticker
    if "ticker" not in df_raw.columns:
        df_raw = df_raw.rename(
            columns={df_raw.columns[0]: "ticker"})

    # Garante coluna tipo
    if "tipo" not in df_raw.columns:
        letras_call = set("ABCDEFGHIJKL")
        df_raw["tipo"] = df_raw["ticker"].apply(
            lambda t: "CALL"
            if len(str(t)) >= 5 and
               str(t)[4].upper() in letras_call
            else "PUT")

    # Strike — está em centavos (13700 = R$137,00)
    if "strike" in df_raw.columns:
        df_raw["strike"] = pd.to_numeric(
            df_raw["strike"], errors="coerce")
        if df_raw["strike"].median() > 1000:
            df_raw["strike"] = df_raw["strike"] / 100

    # Fechamento — está em centavos (3610 = R$36,10)
    if "fechamento" in df_raw.columns:
        df_raw["fechamento"] = pd.to_numeric(
            df_raw["fechamento"].astype(str)
            .str.replace(",","."), errors="coerce")
        if df_raw["fechamento"].median() > 100:
            df_raw["fechamento"] = df_raw["fechamento"] / 100

    # Volume — usa lançamentos como proxy
    if "volume" not in df_raw.columns:
        if "lancamentos" in df_raw.columns:
            df_raw["volume"] = pd.to_numeric(
                df_raw["lancamentos"],
                errors="coerce").fillna(0)
        else:
            df_raw["volume"] = 0
    else:
        df_raw["volume"] = pd.to_numeric(
            df_raw["volume"], errors="coerce").fillna(0)

    # Vencimento e T
    if "vencimento" in df_raw.columns:
        df_raw["vencimento"] = pd.to_datetime(
            df_raw["vencimento"],
            dayfirst=True, errors="coerce")
        df_raw["data"] = pd.to_datetime(data)
        df_raw["T"] = (
            df_raw["vencimento"] -
            df_raw["data"]).dt.days / 365.0
        df_raw["T"] = df_raw["T"].clip(lower=0)

    # Campos obrigatórios
    df_raw["ativo_base"]     = ativo
    df_raw["fonte"]          = "paper"
    df_raw["schema_version"] = SCHEMA_VERSION

    # Gregas — calcula se tiver preço da ação
    if preco_acao and preco_acao > 0:
        df_raw["preco_acao"] = preco_acao
        selic_aa = SELIC_HISTORICA.get(
            pd.to_datetime(data).year, 13.5)
        df_raw["selic"] = selic_aa
        df_raw["r"]     = math.log(1 + selic_aa/100)

        op = df_raw[
            df_raw["tipo"].isin(["CALL","PUT"]) &
            df_raw["fechamento"].notna() &
            (df_raw["fechamento"] > 0) &
            df_raw["strike"].notna() &
            df_raw["T"].notna() &
            (df_raw["T"] > 0)
        ].copy()

        if not op.empty:
            r_val = math.log(1 + selic_aa/100)
            ivs   = _calcular_iv_lote(
                op["fechamento"].values,
                np.full(len(op), preco_acao),
                op["strike"].values,
                op["T"].values,
                np.full(len(op), r_val),
                op["tipo"].tolist())
            sigma = np.where(
                np.isfinite(ivs), ivs, 0.30)
            g = _gregas_vetorizadas(
                np.full(len(op), preco_acao),
                op["strike"].values,
                op["T"].values,
                np.full(len(op), r_val),
                sigma, op["tipo"].tolist())
            for col, vals in [
                    ("iv",    ivs),
                    ("delta", g["delta"]),
                    ("gamma", g["gamma"]),
                    ("theta", g["theta"]),
                    ("vega",  g["vega"])]:
                df_raw.loc[op.index, col] = vals

        df_raw["dist_strike"] = (
            (df_raw["strike"] / preco_acao - 1) * 100
        ).round(2)

    df_raw = df_raw.dropna(
        subset=["ticker","tipo"]).copy()
    print(f"  ✓ {len(df_raw)} opções carregadas")
    return df_raw

def tape_auto(ativos):
    raise NotImplementedError(
        "TAPE.auto não implementado.\n"
        "Disponível quando a API OpLab/opcoes.net.br "
        "for contratada.\n"
        "Use tape_eod_carregar() enquanto isso.")

if __name__ == "__main__":
    print(f"✓ TAPE v1.2 carregado")
    print(f"  Caminhos via Célula 1 — sem redeclaração")
    print(f"  Master JSON: tape_ativo_carregar | tape_ativo_salvar | "
          f"tape_ciclo_salvar | tape_ciclo_para_data")
    print(f"  Dados:       tape_ohlcv_carregar | tape_ibov_carregar | tape_externa_carregar")
    print(f"  Backtest:    tape_historico_carregar | tape_eod_carregar | tape_auto")
    print(f"  REFLECT:     funções movidas para EDGE (reflect_*)")
    print(f"  SCAN aberto: protocolo retomada após estado E não definido")
