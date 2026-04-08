# atlas_backend/core/dc_runner.py
"""
Executor de subprocessos do Delta Chaos.
Único ponto de integração entre ATLAS e Delta Chaos.

edge.py          FAZ o trabalho — modos atômicos, autossuficientes
dc_runner.py     APERTA o botão — protocolo ATLAS↔Delta Chaos
delta_chaos.py   EXPÕE o botão — endpoints HTTP apenas
"""

import asyncio
import json
import os
import sys
import threading
import time
from datetime import date, datetime
from pathlib import Path
from typing import AsyncIterator, Optional

from atlas_backend.core.paths import get_paths
from atlas_backend.core.terminal_stream import emit_log, emit_error
from atlas_backend.core.audit_logger import log_action
from atlas_backend.core.event_bus import emit_dc_event

# Controle de concorrência global
_dc_running: bool = False

# ── DEBUG: limitar a um único ativo para testes ──
DEBUG_TICKER = "PETR4"   # None = roda todos

def _get_dc_script() -> Path:
    paths = get_paths()
    dc_dir = paths.get("delta_chaos_dir")
    if not dc_dir:
        raise FileNotFoundError(
            "Campo 'delta_chaos_dir' ausente no paths.json. "
            "Configure o diretório corretamente."
        )

    script = Path(dc_dir) / "edge.py"
    if not script.exists():
        raise FileNotFoundError(
            f"edge.py não encontrado em: {dc_dir}. "
        )

    return script

async def _stream_subprocess(
    args: list[str],
    cwd: Path,
    action_name: str,
    action_payload: dict,
    modulo: Optional[str] = None
) -> dict:
    """
    Executa subprocesso do Delta Chaos e emite eventos estruturados.

    O dc_runner parseia o stdout para detectar transições de módulo
    (TAPE → ORBIT → FIRE) e emite eventos a partir do processo uvicorn.

    Args:
        modulo: Nome do módulo para eventos ("TAPE", "ORBIT", "FIRE", etc.)
                Se None, não emite eventos (comportamento legacy).
    """

    full_output = []

    # Diretório compartilhado para eventos JSONL
    ATLAS_ROOT = Path(__file__).resolve().parent.parent.parent
    TMP_DIR = ATLAS_ROOT / "tmp"
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    # ── Emitir evento de início do módulo ──
    # REMOVIDO: O _watch_events já emite dc_module_start ao ler do JSONL do subprocess
    # Emitir manualmente causava duplicação de eventos no frontend
    # if modulo:
    #     emit_dc_event("dc_module_start", modulo, "running", **action_payload)

    main_loop = asyncio.get_running_loop()

    def _watch_events(event_log_path, action_payload, stop_event):
        """Lê arquivo JSONL continuamente e emite eventos ATLAS."""
        last_pos = 0
        while not stop_event.is_set():
            try:
                if event_log_path.exists():
                    with open(event_log_path, "r", encoding="utf-8") as f:
                        f.seek(last_pos)
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            event = json.loads(line)
                            ev_modulo = event.get("modulo")
                            ev_status = event.get("status")
                            
                            if ev_status == "start":
                                emit_dc_event("dc_module_start", ev_modulo, "running", **action_payload)
                            elif ev_status == "done":
                                emit_dc_event("dc_module_complete", ev_modulo, "ok", **action_payload)
                            elif ev_status == "error":
                                emit_dc_event("dc_module_complete", ev_modulo, "error", **action_payload)
                        last_pos = f.tell()
            except Exception:
                pass
            time.sleep(0.5)

    def _sync_runner():
        import subprocess

        env = os.environ.copy()
        # Garante que o python vai enxergar a raiz do ATLAS como import root pra rodar o module 'delta_chaos'
        env["PYTHONPATH"] = str(cwd.parent)
        # Força o Windows a renderizar prints com UTF-8 nativamente para as setas e cores do terminal não crasharem
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        # Gerar run_id único e passar para subprocesso
        run_id = f"dc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        event_log_path = TMP_DIR / f"events_{run_id}.jsonl"
        env["ATLAS_RUN_ID"] = run_id

        # Iniciar watcher de eventos em thread separada
        stop_event = threading.Event()
        watch_thread = threading.Thread(
            target=_watch_events,
            args=(event_log_path, action_payload, stop_event),
            daemon=True
        )
        watch_thread.start()

        proc = subprocess.Popen(
            [sys.executable] + args,
            cwd=str(cwd.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env
        )

        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            full_output.append(line)

            lvl = "info"
            if line.startswith("ERRO") or line.startswith("✗") or "Error" in line:
                lvl = "error"
            elif line.startswith("⚠") or line.startswith("~"):
                lvl = "warning"
            
            main_loop.call_soon_threadsafe(emit_log, line, lvl)

        proc.wait()
        
        # Parar watcher e esperar thread terminar
        stop_event.set()
        watch_thread.join(timeout=2)
        
        # Cleanup do arquivo de eventos (exceto se DEBUG)
        if not DEBUG_TICKER and event_log_path.exists():
            try:
                event_log_path.unlink()
            except Exception:
                pass
        
        return proc.returncode

    try:
        returncode = await asyncio.wait_for(asyncio.to_thread(_sync_runner), timeout=1800)

        output_str = "\n".join(full_output)
        
        # Verificar se há erros no output
        tem_erro = any(
            line.startswith("ERRO") or "Error" in line or "Traceback" in line
            for line in full_output
        )
        
        status = "ERRO" if (returncode != 0 or tem_erro) else "OK"
        
        # ── Emitir evento de conclusão do módulo principal ──
        if modulo:
            dc_status = "ok" if status == "OK" else "error"
            emit_dc_event("dc_module_complete", modulo, dc_status, **action_payload)
        
        if tem_erro and returncode == 0:
            emit_log("[DAILY] ⚠ Processo completou mas com warnings", level="warning")

        log_action(
            action=action_name,
            payload=action_payload,
            response={
                "status": status,
                "returncode": returncode,
                "linhas": len(full_output)
            }
        )

        return {
            "status": status,
            "returncode": returncode,
            "output": output_str
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        emit_error(repr(e))
        log_action(
            action=action_name,
            payload=action_payload,
            response={"status": "ERRO", "error": repr(e)}
        )
        raise


def _validar_caminho(caminho: str) -> None:
    paths = get_paths()
    base = Path(paths.get("delta_chaos_base", ""))
    try:
        Path(caminho).resolve().relative_to(base.resolve())
    except ValueError:
        raise ValueError(f"CRÍTICO: Caminho de arquivo tenta escapar do root base directory: {base}")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers privados do orquestrador
# ─────────────────────────────────────────────────────────────────────────────

def _detectar_xlsx(ticker: str) -> Optional[str]:
    """Retorna path do xlsx se existe, None se não."""
    paths = get_paths()
    opcoes_dir = paths.get("opcoes_hoje_dir", "")
    if not opcoes_dir:
        return None
    xlsx_path = os.path.join(opcoes_dir, f"{ticker}.xlsx")
    return xlsx_path if os.path.exists(xlsx_path) else None


def _ciclo_mudou(ticker: str) -> bool:
    """Compara mês do OHLCV cache com último ciclo do historico."""
    import pandas as pd
    try:
        paths = get_paths()
        ohlcv_dir = paths.get("ohlcv_dir", "")
        parquet_path = os.path.join(ohlcv_dir, f"{ticker}.parquet")
        if not os.path.exists(parquet_path):
            return True  # Sem cache → ciclo mudou
        df = pd.read_parquet(parquet_path)
        ohlcv_month = df.index.max().strftime("%Y-%m")
        from atlas_backend.core.delta_chaos_reader import get_ativo
        dados_ativo = get_ativo(ticker)
        historico = dados_ativo.get("historico", [])
        if not historico:
            return True  # Sem histórico → ciclo mudou
        ultimo_ciclo = historico[-1].get("ciclo_id", "")
        if not ultimo_ciclo:
            return True
        return ohlcv_month > ultimo_ciclo
    except Exception:
        return True  # Em caso de erro, força atualização


def _ler_posicao_aberta(ticker: str) -> Optional[dict]:
    """Lê book_paper.json e retorna posição aberta do ticker."""
    try:
        paths = get_paths()
        book_path = os.path.join(paths.get("book_dir", ""), "book_paper.json")
        if not os.path.exists(book_path):
            return None
        import json
        with open(book_path, "r", encoding="utf-8") as f:
            book = json.load(f)
        ops = book.get("ops", [])
        for op in ops:
            if op.get("ativo") == ticker and op.get("data_saida") is None:
                return op
        return None
    except Exception:
        return None


def _verificar_tp_stop(ticker: str, posicao: dict, xlsx_path: str) -> dict:
    """Lê preço atual do xlsx e calcula pnl vs take_profit/stop_loss."""
    try:
        import pandas as pd
        df = pd.read_excel(xlsx_path, header=1)
        # Normaliza nomes de colunas
        df.columns = [str(c).strip().replace("\xa0", "") for c in df.columns]
        # Busca ticker no xlsx
        ticker_col = None
        for col in df.columns:
            if "ativo" in col.lower() or "ticker" in col.lower() or "código" in col.lower():
                ticker_col = col
                break
        if not ticker_col:
            return {"fechar": False, "motivo": "coluna ativo não encontrada", "pnl": 0.0}
        row = df[df[ticker_col].astype(str).str.contains(ticker.replace(".SA", ""), na=False)]
        if row.empty:
            return {"fechar": False, "motivo": "ticker não encontrado no xlsx", "pnl": 0.0}
        preco_atual = float(row.iloc[0].get("Último", row.iloc[0].get("Preço", 0)))
        preco_entrada = posicao.get("preco_entrada", 0)
        take_profit = posicao.get("take_profit", 0)
        stop_loss = posicao.get("stop_loss", 0)
        if preco_entrada <= 0:
            return {"fechar": False, "motivo": "preco_entrada inválido", "pnl": 0.0}
        pnl_pct = (preco_atual - preco_entrada) / preco_entrada * 100
        fechar = False
        motivo = ""
        if take_profit and preco_atual >= take_profit:
            fechar = True
            motivo = f"TP atingido ({preco_atual:.2f} >= {take_profit:.2f})"
        elif stop_loss and preco_atual <= stop_loss:
            fechar = True
            motivo = f"SL atingido ({preco_atual:.2f} <= {stop_loss:.2f})"
        return {"fechar": fechar, "motivo": motivo, "pnl": pnl_pct}
    except Exception as e:
        return {"fechar": False, "motivo": f"erro: {str(e)}", "pnl": 0.0}


def _tune_elegivel(ticker: str) -> bool:
    """Verifica se TUNE é elegível (>= 126 dias úteis desde último TUNE)."""
    try:
        from pandas import bdate_range
        from atlas_backend.core.delta_chaos_reader import get_ativo
        dados_ativo = get_ativo(ticker)
        historico_config = dados_ativo.get("historico_config", [])
        tunes = [c["data"] for c in historico_config if "TUNE" in c.get("modulo", "")]
        if not tunes:
            return True  # Sem histórico → elegível
        last_tune = max(tunes)
        dias_uteis = len(bdate_range(last_tune, date.today()))
        return dias_uteis >= 126
    except Exception:
        return False


async def _verificar_dados(ticker: str, ano: int, mes: int) -> dict:
    """Verifica dados disponíveis (simplificado - retorna True para tudo)."""
    # TODO: implementar verificação real via tape_verificar_dados() quando modo existir
    return {"cotahist": True, "selic": True, "ohlcv": True}


# ─────────────────────────────────────────────────────────────────────────────
# Orquestrador — lógica de sequência completa
# ─────────────────────────────────────────────────────────────────────────────

async def dc_daily(tickers: list) -> dict:
    """
    Sequencia todos os modos do Delta Chaos para cada ticker.
    
    Fluxo:
      [DIÁRIO]
      1. verificar dados disponíveis
      2. reflect_daily se xlsx presente
      3. posição aberta? → verificar TP/STOP
      4. gate_eod
      [MENSAL — se ciclo mudou]
      5. orbit (se dados OK)
      6. backtest_gate
      7. tune (se elegível)
    """
    digest = {}
    
    # ── DEBUG: limitar a um único ativo para testes ──
    if DEBUG_TICKER:
        if DEBUG_TICKER in tickers:
            tickers = [DEBUG_TICKER]
            emit_log(f"[DAILY] ⚠ MODO DEBUG — processando apenas {DEBUG_TICKER}", level="warning")
        elif DEBUG_TICKER not in tickers:
            emit_log(f"[DAILY] ⚠ DEBUG_TICKER={DEBUG_TICKER} não encontrado em ativos", level="warning")
    
    emit_log("[DAILY] 🚀 Iniciando ciclo de manutenção...", level="info")
    emit_log(f"[DAILY] Verificando {len(tickers)} ativos...", level="info")

    for ticker in tickers:
        emit_log(f"[DAILY] Processando {ticker}...", level="info")
        ticker_digest = {"ticker": ticker}

        # ═══ NOVO: Verificar se ativo tem GATE aprovado no historico_config ═══
        from atlas_backend.core.delta_chaos_reader import get_ativo
        dados = get_ativo(ticker)
        gate_ok = any(
            "GATE" in c.get("modulo", "") or c.get("parametro") == "gate_inicial"
            for c in dados.get("historico_config", [])
        )
        if not gate_ok:
            emit_log(f"[DAILY] {ticker}: onboarding incompleto — aguardando GATE", level="warning")
            # ═══ NOVO: Emitir evento para frontend mostrar GATE vermelho ═══
            emit_dc_event("dc_module_complete", "GATE", "error",
                          ticker=ticker, descricao="onboarding incompleto — aguardando GATE")
            # ═══ FIM NOVO ═══
            ticker_digest["motivo"] = "onboarding incompleto — aguardando GATE"
            digest[ticker] = ticker_digest
            continue
        # ═══ FIM NOVO ═══

        # [DIÁRIO]
        # 1. verificar dados disponíveis
        dados_ok = await _verificar_dados(ticker, date.today().year, date.today().month)

        # 2. reflect_daily se xlsx presente
        xlsx_path = _detectar_xlsx(ticker)
        if xlsx_path:
            emit_log(f"[DAILY] {ticker}: xlsx encontrado, rodando reflect_daily", level="info")
            try:
                await dc_reflect_daily(ticker, xlsx_path)
            except Exception as e:
                emit_log(f"[DAILY] {ticker}: reflect_daily erro — {e}", level="error")

        # 3. posição aberta?
        posicao = _ler_posicao_aberta(ticker)
        if posicao:
            ticker_digest["posicao"] = {"aberta": True, "acao": "manter"}
            if xlsx_path:
                resultado = _verificar_tp_stop(ticker, posicao, xlsx_path)
                if resultado["fechar"]:
                    ticker_digest["posicao"] = {"aberta": True, "acao": "fechar", **resultado}
                    emit_log(f"[DAILY] {ticker}: {resultado['motivo']}", level="info")
                    digest[ticker] = ticker_digest
                    continue
                else:
                    ticker_digest["posicao"]["pnl"] = resultado["pnl"]
            emit_log(f"[DAILY] {ticker}: posição aberta — mantendo", level="info")
            digest[ticker] = ticker_digest
            continue

        ticker_digest["posicao"] = {"aberta": False, "acao": "sem_posicao"}

        # 4. gate_eod
        try:
            gate_result = await dc_gate_eod(ticker)
            gate_output = gate_result.get("output", "")
            
            if "BLOQUEADO" in gate_output:
                ticker_digest["gate_eod"] = "BLOQUEADO"
                precisa_bloco_mensal = (
                    "GATE completo nunca executado" in gate_output
                    or "ORBIT defasado" in gate_output
                )
                if precisa_bloco_mensal:
                    emit_dc_event("dc_module_complete", "GATE", "error",
                                  ticker=ticker, descricao="GATE EOD = BLOQUEADO — dados incompletos")
                    emit_log(f"[DAILY] {ticker}: BLOQUEADO — rodando bloco mensal", level="info")
                else:
                    emit_dc_event("dc_module_complete", "GATE", "error",
                                  ticker=ticker, descricao="GATE EOD = BLOQUEADO")
                    emit_log(f"[DAILY] {ticker}: BLOQUEADO — pulando", level="info")
                    digest[ticker] = ticker_digest
                    continue
            elif "OPERAR" in gate_output:
                ticker_digest["gate_eod"] = "OPERAR"
                emit_dc_event("dc_module_complete", "GATE", "ok",
                              ticker=ticker, descricao="GATE EOD = OPERAR")
                emit_log(f"[DAILY] {ticker}: gate_eod = OPERAR", level="info")
            elif "MONITORAR" in gate_output:
                ticker_digest["gate_eod"] = "MONITORAR"
                emit_dc_event("dc_module_complete", "GATE", "ok",
                              ticker=ticker, descricao="GATE EOD = MONITORAR")
                emit_log(f"[DAILY] {ticker}: gate_eod = MONITORAR", level="info")
                digest[ticker] = ticker_digest
                continue
            else:
                ticker_digest["gate_eod"] = gate_output.strip()
        except Exception as e:
            ticker_digest["gate_eod"] = f"erro: {str(e)}"
            emit_log(f"[DAILY] {ticker}: gate_eod erro — {e}", level="error")
            digest[ticker] = ticker_digest
            continue

        # Se gate_eod = OPERAR → aguarda CEO, fim do fluxo diário
        if ticker_digest.get("gate_eod") == "OPERAR":
            digest[ticker] = ticker_digest
            continue

        # [MENSAL — se ciclo mudou]
        if _ciclo_mudou(ticker):
            emit_log(f"[DAILY] {ticker}: ciclo mudou — executando bloco mensal", level="info")
            bloco_mensal = {"orbit": None, "tune": None}

            # 5. orbit
            if not dados_ok.get("cotahist", False):
                bloco_mensal["orbit"] = "postergado — COTAHIST indisponível"
                ticker_digest["bloco_mensal"] = bloco_mensal
                digest[ticker] = ticker_digest
                continue

            try:
                orbit_result = await dc_orbit_update(ticker)
                if orbit_result["status"] != "OK":
                    bloco_mensal["orbit"] = f"erro: {orbit_result['output']}"
                    ticker_digest["bloco_mensal"] = bloco_mensal
                    digest[ticker] = ticker_digest
                    continue
                bloco_mensal["orbit"] = "ok"
                emit_log(f"[DAILY] {ticker}: orbit update ok", level="info")
                # Emitir evento para ORBIT
                emit_dc_event("dc_module_complete", "ORBIT", "ok",
                              ticker=ticker, descricao="ORBIT atualizado")
            except Exception as e:
                bloco_mensal["orbit"] = f"erro: {str(e)}"
                ticker_digest["bloco_mensal"] = bloco_mensal
                digest[ticker] = ticker_digest
                continue

            # 6. TUNE REMOVIDO do Check Status — executado apenas na Gestão via endpoint
            # if _tune_elegivel(ticker):
            #     try:
            #         await dc_tune(ticker)
            #         bloco_mensal["tune"] = "executado"
            #         emit_log(f"[DAILY] {ticker}: TUNE executado", level="info")
            #     except Exception as e:
            #         bloco_mensal["tune"] = f"erro: {str(e)}"
            #         emit_log(f"[DAILY] {ticker}: TUNE erro — {e}", level="error")
            # else:
            #     bloco_mensal["tune"] = "pulado — não elegível"
            bloco_mensal["tune"] = "executado via Gestão"

            ticker_digest["bloco_mensal"] = bloco_mensal

            # Após bloco mensal executado, marcar GATE como completo (verde)
            emit_dc_event("dc_module_complete", "GATE", "ok",
                          ticker=ticker, descricao="Bloco mensal executado — GATE atualizado")

        digest[ticker] = ticker_digest

        # #3 FIX: Emitir evento quando cada ativo termina - permite atualizar UI durante ciclo
        emit_dc_event("daily_ativo_complete", "DAILY", "ok",
                      ticker=ticker, digest=ticker_digest)

    emit_log(f"[DAILY] ✅ Ciclo de manutenção concluído — {len(digest)} ativos processados", level="info")
    return digest


# ─────────────────────────────────────────────────────────────────────────────
# Modos atômicos — um subprocess por função
# ─────────────────────────────────────────────────────────────────────────────

async def dc_eod(xlsx_dir: str) -> dict:
    _validar_caminho(xlsx_dir)
    script = _get_dc_script()
    return await _stream_subprocess(
        args=["-m", "delta_chaos.edge", "--modo", "eod", "--xlsx_dir", xlsx_dir],
        cwd=script.parent,
        action_name="dc_eod_executar",
        action_payload={"xlsx_dir": xlsx_dir},
        modulo=None  # EOD não é um módulo principal do fluxo TAPE→ORBIT→FIRE
    )

async def dc_orbit_backtest(ticker: str, anos: Optional[list] = None) -> dict:
    """Onboarding: modo pesado — COTAHIST + ORBIT completo (backtest_dados)."""
    script = _get_dc_script()
    args = ["-m", "delta_chaos.edge", "--modo", "backtest_dados", "--ticker", ticker]
    if anos:
        args += ["--anos", ",".join(str(a) for a in anos)]
    return await _stream_subprocess(
        args=args,
        cwd=script.parent,
        action_name="dc_orbit",
        action_payload={"ticker": ticker, "anos": anos},
        modulo="ORBIT"
    )

async def dc_tune(ticker: str) -> dict:
    script = _get_dc_script()
    return await _stream_subprocess(
        args=["-m", "delta_chaos.edge", "--modo", "tune", "--ticker", ticker],
        cwd=script.parent,
        action_name="dc_tune",
        action_payload={"ticker": ticker},
        modulo=None  # TUNE é configuração, não módulo do fluxo principal
    )

async def dc_gate_backtest(ticker: str) -> dict:
    """Executa GATE via backtest completo (8 etapas) para atualização mensal."""
    script = _get_dc_script()
    return await _stream_subprocess(
        args=["-m", "delta_chaos.edge", "--modo", "backtest_gate", "--ticker", ticker],
        cwd=script.parent,
        action_name="dc_backtest_gate",
        action_payload={"ticker": ticker},
        modulo="GATE"
    )

async def dc_orbit_update(ticker: str, anos: Optional[list] = None) -> dict:
    script = _get_dc_script()
    args = ["-m", "delta_chaos.edge", "--modo", "orbit_update", "--ticker", ticker]
    if anos:
        args += ["--anos", ",".join(str(a) for a in anos)]
    return await _stream_subprocess(
        args=args,
        cwd=script.parent,
        action_name="dc_orbit_update",
        action_payload={"ticker": ticker, "anos": anos},
        modulo="ORBIT"
    )

async def dc_reflect_daily(ticker: str, xlsx_path: str) -> dict:
    script = _get_dc_script()
    return await _stream_subprocess(
        args=["-m", "delta_chaos.edge", "--modo", "reflect_daily",
              "--ticker", ticker, "--xlsx_path", xlsx_path],
        cwd=script.parent,
        action_name="dc_reflect_daily",
        action_payload={"ticker": ticker, "xlsx_path": xlsx_path}
    )

async def dc_gate_eod(ticker: str) -> dict:
    script = _get_dc_script()
    return await _stream_subprocess(
        args=["-m", "delta_chaos.edge", "--modo", "gate_eod", "--ticker", ticker],
        cwd=script.parent,
        action_name="dc_gate_eod",
        action_payload={"ticker": ticker},
        modulo="GATE"
    )
