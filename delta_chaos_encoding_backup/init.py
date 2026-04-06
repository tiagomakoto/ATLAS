# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# DELTA CHAOS â€” INIT v2.0
# AlteraÃ§Ãµes em relaÃ§Ã£o Ã  v1.0:
# MIGRADO (P1): removida dependÃªncia do Google Colab
#   â€” DRIVE_BASE lido de atlas_backend/config/paths.json
#   â€” Fallback: ~/DeltaChaos se paths.json nÃ£o encontrado
# MIGRADO (P5): prints de inicializaÃ§Ã£o sob if __name__ == "__main__"
# MANTIDO: todos os caminhos derivados, carregar_config, cfg_global
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

import json
import os
import json
import glob
from pathlib import Path

import pandas as pd

# â”€â”€ Logging ATLAS (graceful fallback) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    from atlas_backend.core.terminal_stream import emit_log, emit_error
    _atlas_disponivel = True
except ImportError:
    def emit_log(msg, level="info"): print(f"[{level.upper()}] {msg}")
    def emit_error(e): print(f"[ERROR] {e}")
    _atlas_disponivel = False


# â”€â”€ P1 â€” Leitura de DRIVE_BASE do paths.json â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _carregar_paths() -> dict:
    """
    LÃª paths.json do diretÃ³rio de config do ATLAS.
    Fallback: ~/DeltaChaos se paths.json nÃ£o encontrado.
    """
    paths_file = (
        Path(__file__).parent.parent
        / "atlas_backend" / "config" / "paths.json"
    )
    if paths_file.exists():
        with open(paths_file, encoding="utf-8") as f:
            return json.load(f)
    return {"delta_chaos_base": str(Path.home() / "DeltaChaos")}


_paths     = _carregar_paths()
DRIVE_BASE = _paths.get(
    "delta_chaos_base",
    str(Path.home() / "DeltaChaos")
)

# â”€â”€ Caminhos â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
TAPE_DIR             = os.path.join(DRIVE_BASE, "TAPE")
COTAHIST_DIR         = os.path.join(TAPE_DIR,   "cotahist")
GREGAS_DIR           = os.path.join(TAPE_DIR,   "gregas")
OHLCV_DIR            = os.path.join(TAPE_DIR,   "ohlcv")
EXTERNAS_DIR         = os.path.join(TAPE_DIR,   "externas")
SELIC_CACHE          = os.path.join(TAPE_DIR,   "selic_historica.parquet")
ORBIT_DIR            = os.path.join(DRIVE_BASE, "ORBIT")
TRADELOG_DIR         = os.path.join(DRIVE_BASE, "TradeLog")
BOOK_DIR             = os.path.join(DRIVE_BASE, "BOOK")
OPCOES_HOJE_DIR      = os.path.join(DRIVE_BASE, "opcoes_hoje")
OPCOES_HISTORICO_DIR = os.path.join(DRIVE_BASE, "opcoes_historico")
ATIVOS_DIR           = os.path.join(DRIVE_BASE, "ativos")

DIRETORIOS = {
    "Delta Chaos":      DRIVE_BASE,
    "TAPE":             TAPE_DIR,
    "TAPE/cotahist":    COTAHIST_DIR,
    "TAPE/gregas":      GREGAS_DIR,
    "TAPE/ohlcv":       OHLCV_DIR,
    "TAPE/externas":    EXTERNAS_DIR,
    "ORBIT":            ORBIT_DIR,
    "TradeLog":         TRADELOG_DIR,
    "BOOK":             BOOK_DIR,
    "opcoes_hoje":      OPCOES_HOJE_DIR,
    "ativos":           ATIVOS_DIR,
    "opcoes_historico": OPCOES_HISTORICO_DIR,
}

# â”€â”€ FunÃ§Ãµes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def verificar_diretorios():
    emit_log("DiretÃ³rios:")
    todos_ok = True
    for nome, path in DIRETORIOS.items():
        if os.path.exists(path):
            n = len(os.listdir(path))
            emit_log(f"  âœ“ {nome:25} ({n} arquivos)")
        else:
            try:
                os.makedirs(path, exist_ok=True)
                emit_log(f"  + criado    {nome:25} â†’ {path}")
            except Exception as e:
                emit_error(f"  âœ— falhou    {nome:25} â†’ {e}")
                todos_ok = False
    return todos_ok


def verificar_cache():
    emit_log("Cache:")

    # COTAHISTs
    if os.path.exists(COTAHIST_DIR):
        txts = sorted([f for f in os.listdir(COTAHIST_DIR)
                       if f.endswith(".TXT")])
        if txts:
            for f in txts:
                mb = os.path.getsize(
                    os.path.join(COTAHIST_DIR, f)) / 1e6
                ok = "âœ“" if mb >= 50 else "âš "
                emit_log(f"    {ok} {f:35} {mb:6.0f} MB")
        else:
            emit_log("    ~ cotahist: nenhum arquivo")

    # Gregas
    if os.path.exists(GREGAS_DIR):
        parquets = sorted([f for f in os.listdir(GREGAS_DIR)
                           if f.endswith(".parquet")])
        if parquets:
            for f in parquets:
                mb = os.path.getsize(
                    os.path.join(GREGAS_DIR, f)) / 1e6
                ok = "âœ“" if mb >= 1 else "âš "
                emit_log(f"    {ok} {f:35} {mb:5.1f} MB")
        else:
            emit_log("    ~ gregas: nenhum arquivo")

    # OHLCV
    if os.path.exists(OHLCV_DIR):
        parquets = sorted([f for f in os.listdir(OHLCV_DIR)
                           if f.endswith(".parquet")])
        if parquets:
            for f in parquets:
                mb = os.path.getsize(
                    os.path.join(OHLCV_DIR, f)) / 1e6
                emit_log(f"    âœ“ {f:35} {mb:5.1f} MB")
        else:
            emit_log("    ~ ohlcv: nenhum arquivo")

    # Externas
    if os.path.exists(EXTERNAS_DIR):
        parquets = sorted([f for f in os.listdir(EXTERNAS_DIR)
                           if f.endswith(".parquet")])
        if parquets:
            for f in parquets:
                mb = os.path.getsize(
                    os.path.join(EXTERNAS_DIR, f)) / 1e6
                emit_log(f"    âœ“ {f:35} {mb:5.1f} MB")
        else:
            emit_log("    ~ externas: nenhum arquivo")

    # SELIC
    if os.path.exists(SELIC_CACHE):
        mb = os.path.getsize(SELIC_CACHE) / 1e6
        try:
            df_s = pd.read_parquet(SELIC_CACHE)
            df_s["data"] = pd.to_datetime(df_s["data"])
            ano_min = df_s["data"].dt.year.min()
            ano_max = df_s["data"].dt.year.max()
            ok = "âœ“" if mb >= 0.05 else "âš "
            emit_log(
                f"    {ok} {'selic_historica.parquet':35} "
                f"{mb:5.2f} MB "
                f"({ano_min}â†’{ano_max}, {len(df_s):,} dias)"
            )
        except Exception:
            emit_log("    âš  selic_historica.parquet corrompido")
    else:
        emit_log("    ~ selic_historica.parquet: nÃ£o encontrado")

    # Ativos master JSONs
    if os.path.exists(ATIVOS_DIR):
        jsons = sorted([f for f in os.listdir(ATIVOS_DIR)
                        if f.endswith(".json")])
        if jsons:
            for f in jsons:
                mb = os.path.getsize(
                    os.path.join(ATIVOS_DIR, f)) / 1e6
                try:
                    with open(os.path.join(ATIVOS_DIR, f)) as fh:
                        dados = json.load(fh)
                    n_ciclos = len(dados.get("historico", []))
                    emit_log(
                        f"    âœ“ {f:35} {mb:5.2f} MB "
                        f"({n_ciclos} ciclos)"
                    )
                except Exception:
                    emit_log(f"    âš  {f} corrompido")
        else:
            emit_log("    ~ ativos: nenhum master JSON")

    # Parquets SELIC fragmentados â€” limpa automaticamente
    fragmentados = [
        f for f in glob.glob(
            os.path.join(TAPE_DIR, "selic_*.parquet"))
        if "historica" not in f
    ]
    if fragmentados:
        emit_log("  âš  Parquets SELIC fragmentados â€” removendo:")
        for f in fragmentados:
            mb = os.path.getsize(f) / 1e6
            os.remove(f)
            emit_log(
                f"    âœ“ Removido: {os.path.basename(f)} "
                f"({mb:.2f} MB)"
            )


# â”€â”€ Config global â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CONFIG_PATH = os.path.join(DRIVE_BASE, "delta_chaos_config.json")

CAPITAL_PADRAO = 10000.0


def carregar_config() -> dict:
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        
        if "backtest" not in config:
            config["backtest"] = {}
        if "capital" not in config.get("backtest", {}):
            config["backtest"]["capital"] = CAPITAL_PADRAO
        
        return config
    except FileNotFoundError:
        emit_error(f"delta_chaos_config.json nao encontrado: {CONFIG_PATH}")
        raise


def cfg_global(secao: str, chave: str):
    config = carregar_config()
    if secao in config:
        return config[secao].get(chave)
    return None


# â”€â”€ ExecuÃ§Ã£o standalone â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if __name__ == "__main__":
    print("â•" * 55)
    print("  DELTA CHAOS â€” VerificaÃ§Ã£o de ambiente")
    print("â•" * 55)
    print(f"  DRIVE_BASE: {DRIVE_BASE}")

    dir_ok = verificar_diretorios()

    try:
        verificar_cache()
    except Exception as e:
        print(f"  âš  Erro ao verificar cache: {e}")

    print("\n" + "â•" * 55)
    print(
        "  âœ“ Ambiente OK â€” pode executar as cÃ©lulas TAPE"
        if dir_ok else
        "  âœ— HÃ¡ problemas â€” verifique os erros acima"
    )
    print("â•" * 55)
    print("âœ“ INIT v2.0 carregado")
    print("  DRIVE_BASE lido de paths.json (sem Google Colab)")
    print("  carregar_config e cfg_global disponÃ­veis")
