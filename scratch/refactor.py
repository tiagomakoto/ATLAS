import os
import re

EDGE_PATH = "c:/Users/tiago/OneDrive/Documentos/ATLAS/delta_chaos/edge.py"
DC_RUNNER_PATH = "c:/Users/tiago/OneDrive/Documentos/ATLAS/atlas_backend/core/dc_runner.py"

with open(EDGE_PATH, "r", encoding="utf-8") as f:
    edge_code = f.read()

# 1. Update logging and events in edge.py
edge_code = re.sub(
    r"# Diretório compartilhado para eventos JSONL.*?(def emit_dc_event.*?:\s*pass)",
    r"""# ── Logging ATLAS ─────────────────────────────────
from atlas_backend.core.terminal_stream import emit_log, emit_error
from atlas_backend.core.event_bus import emit_dc_event""",
    edge_code,
    flags=re.DOTALL
)

# Replace emit_event with a wrapper for legacy code to avoid breaking everything before we wrap into functions
emit_event_wrapper = """
def emit_event(modulo, status, ticker=None, **kwargs):
    if status == "start":
        emit_dc_event("dc_module_start", modulo, "running", ticker=ticker, **kwargs)
    elif status == "done":
        emit_dc_event("dc_module_complete", modulo, "ok", ticker=ticker, **kwargs)
    elif status == "error":
        emit_dc_event("dc_module_complete", modulo, "error", ticker=ticker, **kwargs)
    else:
        emit_dc_event("dc_module_complete", modulo, status, ticker=ticker, **kwargs)
"""

edge_code = edge_code.replace("from atlas_backend.core.terminal_stream import emit_log, emit_error\nfrom atlas_backend.core.event_bus import emit_dc_event",
                              "from atlas_backend.core.terminal_stream import emit_log, emit_error\nfrom atlas_backend.core.event_bus import emit_dc_event\n" + emit_event_wrapper)


functions_code = """
# ──────────────────────────────────────────────────────────────
# Funções Públicas Síncronas (API do Orquestrador)
# Requisito SPEC: executam I/O pesado, o caller (dc_runner) deve usar asyncio.to_thread
# ──────────────────────────────────────────────────────────────

def rodar_backtest_dados(ticker: str, anos: list = None):
    try:
        from datetime import datetime
        import sys
        
        anos_list = anos if anos else list(range(2002, datetime.now().year + 1))
        
        emit_dc_event("dc_module_start", "ORBIT", "running", ticker=ticker)
        
        config = carregar_config() or {}
        capital = config.get("backtest", {}).get("capital", 10000.0)
        edge = EDGE(capital=capital, modo="backtest", universo=[ticker])
        
        # TAPE
        emit_dc_event("dc_module_start", "TAPE", "running", ticker=ticker)
        df_tape = tape_historico_carregar(ativos=[ticker], anos=anos_list, forcar=False)
        if df_tape.empty:
            emit_dc_event("dc_module_complete", "TAPE", "error", ticker=ticker, erro="TAPE vazio")
            raise Exception("TAPE vazio")
        externas = tape_externas_carregar([ticker], anos_list)
        emit_dc_event("dc_module_complete", "TAPE", "ok", ticker=ticker, registros=len(df_tape))
        
        # ORBIT
        emit_dc_event("dc_module_start", "ORBIT", "running", ticker=ticker)
        cfg_ativo = tape_ativo_carregar(ticker)
        if cfg_ativo is None:
            emit_dc_event("dc_module_complete", "ORBIT", "error", ticker=ticker, erro="cfg_ativo é None")
            raise Exception(f"Configuração ausente para {ticker}")
            
        orbit = ORBIT(universo={ticker: cfg_ativo})
        df_regimes_result = orbit.orbit_rodar(df_tape, anos_list, modo="mensal", externas_dict=externas)
        if df_regimes_result is None or df_regimes_result.empty:
            emit_dc_event("dc_module_complete", "ORBIT", "error", ticker=ticker, erro="ORBIT vazio")
            raise Exception("ORBIT vazio")
        emit_dc_event("dc_module_complete", "ORBIT", "ok", ticker=ticker)
        
        # REFLECT
        emit_dc_event("dc_module_start", "REFLECT", "running", ticker=ticker)
        try:
            cfg_atual = tape_ativo_carregar(ticker)
            historico_ciclos = list(dict.fromkeys(
                c["ciclo_id"] for c in cfg_atual.get("historico", []) if "ciclo_id" in c
            ))
            reflect_existente = set(cfg_atual.get("reflect_cycle_history", {}).keys())
            ciclos_sem_reflect = [c for c in historico_ciclos if c not in reflect_existente]
            for ciclo_id in ciclos_sem_reflect:
                try:
                    reflect_cycle_calcular(ticker, ciclo_id)
                except Exception as e_ciclo:
                    emit_log(f"~ REFLECT {ciclo_id} ignorado: {e_ciclo}", "warning")
            emit_dc_event("dc_module_complete", "REFLECT", "ok", ticker=ticker)
        except Exception as e:
            emit_dc_event("dc_module_complete", "REFLECT", "error", ticker=ticker, erro=str(e))
            raise e
            
        return {"status": "OK"}
    except Exception as e:
        emit_dc_event("dc_module_complete", "ORBIT", "error", ticker=ticker, erro=str(e))
        import traceback
        traceback.print_exc()
        raise e

def rodar_orbit_update(ticker: str, anos: list = None):
    try:
        from datetime import datetime
        import sys

        anos_list = anos if anos else list(range(2002, datetime.now().year + 1))
        
        # TAPE
        emit_dc_event("dc_module_start", "TAPE", "running", ticker=ticker)
        cfg_ativo = tape_ativo_carregar(ticker)
        df_ohlcv = tape_ohlcv_carregar(ticker, anos_list)
        df_ibov = tape_ibov_carregar(anos_list)
        externas = tape_externas_carregar([ticker], anos_list)
        if df_ohlcv.empty:
            emit_dc_event("dc_module_complete", "TAPE", "error", ticker=ticker, erro="OHLCV vazio")
            raise Exception(f"TAPE: dados OHLCV indisponíveis para {ticker}")
        emit_dc_event("dc_module_complete", "TAPE", "ok", ticker=ticker, registros=len(df_ohlcv))
        
        # ORBIT
        emit_dc_event("dc_module_start", "ORBIT", "running", ticker=ticker)
        orbit = ORBIT(universo={ticker: cfg_ativo})
        orbit.orbit_rodar(df_ohlcv, anos=anos_list, modo="mensal", externas_dict=externas)
        emit_dc_event("dc_module_complete", "ORBIT", "ok", ticker=ticker)
        
        # REFLECT
        emit_dc_event("dc_module_start", "REFLECT", "running", ticker=ticker)
        cfg_atual = tape_ativo_carregar(ticker)
        historico_ciclos = list(dict.fromkeys(
            c["ciclo_id"] for c in cfg_atual.get("historico", []) if "ciclo_id" in c
        ))
        reflect_existente = set(cfg_atual.get("reflect_cycle_history", {}).keys())
        ciclos_sem_reflect = [c for c in historico_ciclos if c not in reflect_existente]
        if not ciclos_sem_reflect:
            ciclos_sem_reflect = [datetime.now().strftime("%Y-%m")]
        for ciclo_id in ciclos_sem_reflect:
            try:
                reflect_cycle_calcular(ticker, ciclo_id)
            except Exception as e_ciclo:
                emit_log(f"~ REFLECT {ciclo_id} ignorado: {e_ciclo}", "warning")
        emit_dc_event("dc_module_complete", "REFLECT", "ok", ticker=ticker)
        return {"status": "OK"}
    except Exception as e:
        emit_dc_event("dc_module_complete", "ORBIT", "error", ticker=ticker, erro=str(e))
        raise e

def rodar_tune(ticker: str):
    from delta_chaos.tune import executar_tune
    emit_dc_event("dc_module_start", "TUNE", "running", ticker=ticker)
    try:
        executar_tune(ticker)
        emit_dc_event("dc_module_complete", "TUNE", "ok", ticker=ticker)
        return {"status": "OK"}
    except Exception as e:
        emit_dc_event("dc_module_complete", "TUNE", "error", ticker=ticker, erro=str(e))
        raise e

def rodar_backtest_gate(ticker: str):
    from delta_chaos.gate import gate_executar
    emit_dc_event("dc_module_start", "GATE", "running", ticker=ticker)
    try:
        resultado = gate_executar(ticker)
        emit_log(f"[GATE] {ticker}: {resultado}", "info")
        emit_dc_event("dc_module_complete", "GATE", "ok", ticker=ticker)
        return {"status": "OK", "output": str(resultado)}
    except Exception as e:
        emit_dc_event("dc_module_complete", "GATE", "error", ticker=ticker, erro=str(e))
        raise e

def rodar_reflect_daily(ticker: str, xlsx_path: str):
    emit_dc_event("dc_module_start", "REFLECT", "running", ticker=ticker)
    try:
        tape_eod_carregar(ativo=ticker, filepath=xlsx_path)
        emit_dc_event("dc_module_complete", "REFLECT", "ok", ticker=ticker)
        return {"status": "OK"}
    except Exception as e:
        emit_dc_event("dc_module_complete", "REFLECT", "error", ticker=ticker, erro=str(e))
        raise e

def rodar_gate_eod(ticker: str):
    emit_dc_event("dc_module_start", "GATE", "running", ticker=ticker)
    try:
        resultado = gate_eod_verificar(ticker, verbose=True)
        emit_log(f"[GATE_EOD] {ticker}: {resultado}", "info")
        emit_dc_event("dc_module_complete", "GATE", "ok", ticker=ticker)
        return {"status": "OK", "output": str(resultado)}
    except Exception as e:
        emit_dc_event("dc_module_complete", "GATE", "error", ticker=ticker, erro=str(e))
        raise e
"""

edge_code = re.sub(r"# ── Entrypoint CLI.*", functions_code + "\n\n# ── Entrypoint CLI — chamado pelo ATLAS via subprocess ───────────\n" + edge_code[edge_code.find("# ── Entrypoint CLI"):], edge_code, count=1, flags=re.DOTALL)

with open(EDGE_PATH, "w", encoding="utf-8") as f:
    f.write(edge_code)

print("edge.py modificado.")


# 2. Modify dc_runner.py
with open(DC_RUNNER_PATH, "r", encoding="utf-8") as f:
    dc_runner_code = f.read()

dc_runner_code = dc_runner_code.replace("from typing import AsyncIterator, Optional", "from typing import AsyncIterator, Optional\nimport delta_chaos.edge as edge")

# Subprocess replacement snippet for dc_runner
# We remove _stream_subprocess totally.
# But dc_eod still needs something. Wait, Q1 the user hadn't answered yet, but the user said "execute o plano".
# I'll just use asyncio.create_subprocess_exec for dc_eod since we deprecated _stream_subprocess.

dc_runner_code = re.sub(r"async def _stream_subprocess.*?return await asyncio.to_thread\(_sync_runner\)", "", dc_runner_code, flags=re.DOTALL)

# Re-implement the public atomic functions
atomic_functions = """
async def dc_eod(xlsx_dir: str) -> dict:
    _validar_caminho(xlsx_dir)
    script = _get_dc_script()
    import subprocess
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-u", "-m", "delta_chaos.edge", "--modo", "eod", "--xlsx_dir", xlsx_dir,
        cwd=str(script.parent.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    stdout, _ = await proc.communicate()
    out_str = stdout.decode('utf-8', errors='replace')
    status = "OK" if proc.returncode == 0 else "ERRO"
    log_action("dc_eod_executar", {"xlsx_dir": xlsx_dir}, {"status": status, "returncode": proc.returncode})
    return {"status": status, "output": out_str, "returncode": proc.returncode}

async def dc_orbit_backtest(ticker: str, anos: Optional[list] = None) -> dict:
    action_payload = {"ticker": ticker, "anos": anos}
    emit_dc_event("dc_module_start", "ORBIT", "running", **action_payload)
    try:
        await asyncio.to_thread(edge.rodar_backtest_dados, ticker, anos)
        emit_dc_event("dc_module_complete", "ORBIT", "ok", **action_payload)
        log_action("dc_orbit", action_payload, {"status": "OK"})
        return {"status": "OK", "returncode": 0, "output": ""}
    except Exception as e:
        emit_dc_event("dc_module_complete", "ORBIT", "error", **action_payload)
        emit_log(f"[ORBIT] {ticker}: erro — {e}", level="error")
        log_action("dc_orbit", action_payload, {"status": "ERRO", "error": repr(e)})
        return {"status": "ERRO", "output": repr(e)}

async def dc_tune(ticker: str) -> dict:
    action_payload = {"ticker": ticker}
    emit_dc_event("dc_module_start", "TUNE", "running", **action_payload)
    
    sqlite_stop = threading.Event()
    db_path = TMP_DIR / f"tune_{ticker}.db"
    
    def _poll_sqlite(db_path, stop_event, action_payload):
        import sqlite3
        import time
        last_count = -1
        TOTAL = 200
        while not stop_event.is_set():
            try:
                if db_path.exists():
                    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=1)
                    try:
                        cur = conn.cursor()
                        cur.execute("SELECT COUNT(*) FROM trial WHERE state = 'COMPLETE'")
                        count = cur.fetchone()[0]
                        cur.execute("SELECT MAX(value) FROM trial WHERE state = 'COMPLETE'")
                        best = cur.fetchone()[0] or 0.0
                    finally:
                        conn.close()

                    if count != last_count:
                        last_count = count
                        emit_dc_event(
                            "dc_tune_progress", "TUNE", "running",
                            trial=count, total=TOTAL, ir=round(float(best), 3), **action_payload
                        )
            except Exception:
                pass
            time.sleep(0.2)
            
    sqlite_thread = threading.Thread(
        target=_poll_sqlite, args=(db_path, sqlite_stop, action_payload), daemon=True
    )
    sqlite_thread.start()
    
    try:
        await asyncio.to_thread(edge.rodar_tune, ticker)
        emit_dc_event("dc_module_complete", "TUNE", "ok", **action_payload)
        log_action("dc_tune", action_payload, {"status": "OK"})
        return {"status": "OK", "returncode": 0, "output": ""}
    except Exception as e:
        emit_dc_event("dc_module_complete", "TUNE", "error", **action_payload)
        emit_log(f"[TUNE] {ticker}: erro — {e}", level="error")
        log_action("dc_tune", action_payload, {"status": "ERRO", "error": repr(e)})
        return {"status": "ERRO", "output": repr(e)}
    finally:
        sqlite_stop.set()
        sqlite_thread.join(timeout=2)

async def dc_gate_backtest(ticker: str) -> dict:
    action_payload = {"ticker": ticker}
    emit_dc_event("dc_module_start", "GATE", "running", **action_payload)
    try:
        res = await asyncio.to_thread(edge.rodar_backtest_gate, ticker)
        emit_dc_event("dc_module_complete", "GATE", "ok", **action_payload)
        log_action("dc_backtest_gate", action_payload, {"status": "OK"})
        return {"status": "OK", "returncode": 0, "output": res.get("output", "")}
    except Exception as e:
        emit_dc_event("dc_module_complete", "GATE", "error", **action_payload)
        emit_log(f"[GATE] {ticker}: erro — {e}", level="error")
        log_action("dc_backtest_gate", action_payload, {"status": "ERRO", "error": repr(e)})
        return {"status": "ERRO", "output": repr(e)}

async def dc_orbit_update(ticker: str, anos: Optional[list] = None) -> dict:
    action_payload = {"ticker": ticker, "anos": anos}
    emit_dc_event("dc_module_start", "ORBIT", "running", **action_payload)
    try:
        await asyncio.to_thread(edge.rodar_orbit_update, ticker, anos)
        emit_dc_event("dc_module_complete", "ORBIT", "ok", **action_payload)
        log_action("dc_orbit_update", action_payload, {"status": "OK"})
        return {"status": "OK", "returncode": 0, "output": ""}
    except Exception as e:
        emit_dc_event("dc_module_complete", "ORBIT", "error", **action_payload)
        emit_log(f"[ORBIT] {ticker}: erro — {e}", level="error")
        log_action("dc_orbit_update", action_payload, {"status": "ERRO", "error": repr(e)})
        return {"status": "ERRO", "output": repr(e)}

async def dc_reflect_daily(ticker: str, xlsx_path: str) -> dict:
    action_payload = {"ticker": ticker, "xlsx_path": xlsx_path}
    emit_dc_event("dc_module_start", "REFLECT", "running", **action_payload)
    try:
        await asyncio.to_thread(edge.rodar_reflect_daily, ticker, xlsx_path)
        emit_dc_event("dc_module_complete", "REFLECT", "ok", **action_payload)
        log_action("dc_reflect_daily", action_payload, {"status": "OK"})
        return {"status": "OK", "returncode": 0, "output": ""}
    except Exception as e:
        emit_dc_event("dc_module_complete", "REFLECT", "error", **action_payload)
        emit_log(f"[REFLECT] {ticker}: erro — {e}", level="error")
        log_action("dc_reflect_daily", action_payload, {"status": "ERRO", "error": repr(e)})
        return {"status": "ERRO", "output": repr(e)}

async def dc_gate_eod(ticker: str) -> dict:
    action_payload = {"ticker": ticker}
    emit_dc_event("dc_module_start", "GATE", "running", **action_payload)
    try:
        res = await asyncio.to_thread(edge.rodar_gate_eod, ticker)
        emit_dc_event("dc_module_complete", "GATE", "ok", **action_payload)
        log_action("dc_gate_eod", action_payload, {"status": "OK"})
        return {"status": "OK", "returncode": 0, "output": res.get("output", "")}
    except Exception as e:
        emit_dc_event("dc_module_complete", "GATE", "error", **action_payload)
        emit_log(f"[GATE] {ticker}: erro — {e}", level="error")
        log_action("dc_gate_eod", action_payload, {"status": "ERRO", "error": repr(e)})
        return {"status": "ERRO", "output": repr(e)}

async def dc_reflect_cycle(ticker: str) -> dict:
    action_payload = {"ticker": ticker}
    emit_dc_event("dc_module_start", "REFLECT", "running", **action_payload)
    try:
        # Reflect cycle internally handled inside orbit_update
        await asyncio.to_thread(edge.rodar_orbit_update, ticker)
        emit_dc_event("dc_module_complete", "REFLECT", "ok", **action_payload)
        log_action("dc_reflect_cycle", action_payload, {"status": "OK"})
        return {"status": "OK", "returncode": 0, "output": ""}
    except Exception as e:
        emit_dc_event("dc_module_complete", "REFLECT", "error", **action_payload)
        emit_log(f"[REFLECT] {ticker}: erro — {e}", level="error")
        log_action("dc_reflect_cycle", action_payload, {"status": "ERRO", "error": repr(e)})
        return {"status": "ERRO", "output": repr(e)}
"""

dc_runner_code = re.sub(
    r"async def dc_eod\(.*?\).*?async def dc_calibracao_iniciar",
    lambda m: atomic_functions + "\nasync def dc_calibracao_iniciar",
    dc_runner_code,
    flags=re.DOTALL
)

# And TMP_DIR is needed in dc_tune for _poll_sqlite
dc_runner_code = dc_runner_code.replace("def _get_dc_script()", 'ATLAS_ROOT = Path(__file__).resolve().parent.parent.parent\nTMP_DIR = ATLAS_ROOT / "tmp"\n\ndef _get_dc_script()')

with open(DC_RUNNER_PATH, "w", encoding="utf-8") as f:
    f.write(dc_runner_code)

print("dc_runner.py modificado.")
