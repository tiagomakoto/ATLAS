# atlas_backend/core/dc_runner.py
"""
Executor de subprocessos do Delta Chaos.
Único ponto de integração entre ATLAS e Delta Chaos.

edge.py FAZ o trabalho — modos atômicos, autossuficientes
dc_runner.py APERTA o botão — protocolo ATLAS↔Delta Chaos
delta_chaos.py EXPÕE o botão — endpoints HTTP apenas
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
DEBUG_TICKER = "VALE3" # None = roda todos

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
        seen_events: set = set()
        while not stop_event.is_set():
    try:
    if event_log_path.exists():
    with open(event_log_path, "r", encoding="utf-8") as f:
    f.seek(last_pos)
    while True:
    line = f.readline()
    if not line:
    break
    last_pos = f.tell()
    line = line.strip()
    if not line:
    continue
    event = json.loads(line)
    ev_modulo = event.get("modulo")
    ev_status = event.get("status")
    ev_ts = event.get("timestamp", "")
    ev_key = (ev_modulo, ev_status, ev_ts)
    if ev_key in seen_events:
    continue
    seen_events.add(ev_key)

    if ev_status == "start":
    emit_dc_event("dc_module_start", ev_modulo, "running", **action_payload)
    elif ev_status == "done":
    emit_dc_event("dc_module_complete", ev_modulo, "ok", **action_payload)
    elif ev_status == "error":
    emit_dc_event("dc_module_complete", ev_modulo, "error", **action_payload)
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
            return True # Sem cache → ciclo mudou
        df = pd.read_parquet(parquet_path)
        ohlcv_month = df.index.max().strftime("%Y-%m")
        from atlas_backend.core.delta_chaos_reader import get_ativo
        dados_ativo = get_ativo(ticker)
        historico = dados_ativo.get("historico", [])
        if not historico:
            return True # Sem histórico → ciclo mudou
        ultimo_ciclo = historico[-1].get("ciclo_id", "")
        if not ultimo_ciclo:
            return True
        return ohlcv_month > ultimo_ciclo
    except Exception:
        return True # Em caso de erro, força atualização


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


def _atualizar_ativo_store(ticker: str) -> None:
    """
    Lê o arquivo JSON do ativo atualizado e envia para o store do frontend.
    Esta função deve ser chamada antes de cada 'continue' no fluxo.
    """
    try:
        from atlas_backend.core.delta_chaos_reader import get_ativo
        dados_atualizados = get_ativo(ticker)
        emit_dc_event("daily_ativo_updated", "DAILY", "ok",
        ticker=ticker, dados=dados_atualizados)
        emit_log(f"[DAILY] {ticker}: ativo atualizado no store", level="debug")
    except Exception as e:
        emit_log(f"[DAILY] {ticker}: erro ao reler arquivo JSON — {e}", level="warning")


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
            return True # Sem histórico → elegível
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

    # ═══ NOVO: Lista de eventos críticos para fallback na resposta da API ═══
    _eventos_criticos = []

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
        ticker_digest = {"ticker": ticker, "xlsx": None}

        # ═══ NOVO: Verificar se ativo tem historico_config (onboarding feito) ═══
        from atlas_backend.core.delta_chaos_reader import get_ativo
        dados = get_ativo(ticker)
        gate_ok = dados.get("historico_config", False) # ← BOOLEANO: true se tem registros
        if not gate_ok:
            emit_log(f"[DAILY] {ticker}: onboarding incompleto — aguardando GATE", level="warning")
            # ═══ NOVO: Emitir evento para frontend mostrar GATE vermelho ═══
            emit_dc_event("dc_module_complete", "GATE", "error",
            ticker=ticker, descricao="onboarding incompleto — aguardando GATE")
            # ═══ NOVO: Adicionar à lista de eventos críticos para fallback na API ═══
            _eventos_criticos.append({
                "type": "dc_module_complete",
                "data": {
                    "modulo": "GATE",
                    "status": "error",
                    "ticker": ticker,
                    "descricao": "onboarding incompleto — aguardando GATE"
                }
            })
            # ═══ FIM NOVO ═══
            # ═══ Item 4: Adicionar gate_eod no digest para ativos bloqueados ═══
            ticker_digest["gate_eod"] = "BLOQUEADO — onboarding não realizado"
            # ═══ FIM ═══
            ticker_digest["motivo"] = "onboarding incompleto — aguardando GATE"
            digest[ticker] = ticker_digest
            continue
        # ═══ FIM NOVO ═══

        # [DIÁRIO]
        # 1. verificar dados disponíveis
        dados_ok = await _verificar_dados(ticker, date.today().year, date.today().month)

        # 2. BLOCO MENSAL (se ciclo mudou)
        if _ciclo_mudou(ticker):
            emit_log(f"[DAILY] {ticker}: ciclo mudou — executando bloco mensal", level="info")
            bloco_mensal = {"orbit": None}

            # TAPE: verificar dados disponíveis
            if not dados_ok.get("cotahist", False):
                bloco_mensal["orbit"] = "postergado — COTAHIST indisponível"
                ticker_digest["bloco_mensal"] = bloco_mensal
                digest[ticker] = ticker_digest
                continue

            # ORBIT
            dados_antes = get_ativo(ticker)
            status_antes = dados_antes.get("status", "SEM_EDGE")
            historico_antes = dados_antes.get("historico", [])
            regime_antes = historico_antes[-1].get("regime", "~") if historico_antes else "~"
            reflect_antes = dados_antes.get("reflect_state", "B")

            try:
                orbit_result = await dc_orbit_update(ticker)
                if orbit_result["status"] != "OK":
                    bloco_mensal["orbit"] = f"erro: {orbit_result['output']}"
                    ticker_digest["bloco_mensal"] = bloco_mensal
                    digest[ticker] = ticker_digest
                    continue

                # Capturar status E regime DEPOIS do ORBIT
                dados_depois = get_ativo(ticker)
                status_depois = dados_depois.get("status", "SEM_EDGE")
                historico_depois = dados_depois.get("historico", [])
                regime_depois = historico_depois[-1].get("regime", "~") if historico_depois else "~"
                reflect_depois = dados_depois.get("reflect_state", "B")

                bloco_mensal["orbit"] = f"{regime_antes} -> {regime_depois}"
                bloco_mensal["orbit_antes"] = regime_antes
                bloco_mensal["orbit_depois"] = regime_depois
                bloco_mensal["status_antes"] = status_antes
                bloco_mensal["status_depois"] = status_depois
                bloco_mensal["reflect_antes"] = reflect_antes
                bloco_mensal["reflect_depois"] = reflect_depois

                emit_log(f"[DAILY] {ticker}: orbit update ok", level="info")
                # REMOVIDO: O watcher já emite dc_module_complete automaticamente
            except Exception as e:
                bloco_mensal["orbit"] = f"erro: {str(e)}"
                ticker_digest["bloco_mensal"] = bloco_mensal
                digest[ticker] = ticker_digest
                continue

        # Após bloco mensal, continuar para XLSX
        ticker_digest["bloco_mensal"] = bloco_mensal
        emit_log(f"[DAILY] {ticker}: bloco mensal concluído, continuando para XLSX", level="info")

        # 3. GATE EOD (apenas avaliação, sem bloco mensal)
        try:
            gate_result = await dc_gate_eod(ticker)
            gate_output = gate_result.get("output", "")
            if "BLOQUEADO" in gate_output:
                ticker_digest["gate_eod"] = "BLOQUEADO"
                # Não executar bloco mensal aqui — ele é disparado por _ciclo_mudou
                emit_dc_event("dc_module_complete", "GATE", "error",
                ticker=ticker, descricao="GATE EOD = BLOQUEADO")
                emit_log(f"[DAILY] {ticker}: BLOQUEADO — aguardando atualização de ciclo", level="info")
            elif "OPERAR" in gate_output:
                ticker_digest["gate_eod"] = "OPERAR"
                emit_log(f"[DAILY] {ticker}: gate_eod = OPERAR", level="info")
            elif "MONITORAR" in gate_output:
                ticker_digest["gate_eod"] = "MONITORAR"
                emit_log(f"[DAILY] {ticker}: gate_eod = MONITORAR", level="info")
            else:
                ticker_digest["gate_eod"] = gate_output.strip()
        except Exception as e:
            ticker_digest["gate_eod"] = f"erro: {str(e)}"
            emit_log(f"[DAILY] {ticker}: gate_eod erro — {e}", level="error")
            digest[ticker] = ticker_digest
            continue

        # 4. XLSX EOD
        xlsx_path = _detectar_xlsx(ticker)
        if xlsx_path:
            emit_log(f"[DAILY] {ticker}: xlsx encontrado, rodando reflect_daily", level="info")
            emit_dc_event("dc_module_complete", "XLSX", "ok",
            ticker=ticker, descricao="XLSX EOD encontrado")
            try:
                await dc_reflect_daily(ticker, xlsx_path)
            except Exception as e:
                emit_log(f"[DAILY] {ticker}: reflect_daily erro — {e}", level="error")
                emit_dc_event("dc_module_complete", "XLSX", "erro",
                ticker=ticker, descricao=f"reflect_daily erro: {e}")
        else:
            emit_log(f"[DAILY] {ticker}: xlsx não encontrado", level="warning")
            emit_dc_event("dc_module_complete", "XLSX", "erro",
            ticker=ticker, descricao="XLSX EOD não encontrado")

        # Preencher campo xlsx no digest
        ticker_digest["xlsx"] = "ok" if xlsx_path else "não encontrado"

        # 5. posição/TP-STOP
        posicao = _ler_posicao_aberta(ticker)
        if posicao:
            ticker_digest["posicao"] = {"aberta": True, "acao": "manter"}
            if xlsx_path:
                resultado = _verificar_tp_stop(ticker, posicao, xlsx_path)
                if resultado["fechar"]:
                    ticker_digest["posicao"] = {
                        "aberta": True,
                        "acao": "fechar",
                        "tp_stop_status": "fechar",
                        "xlsx_lido": True,
                        "motivo": resultado.get("motivo", ""),
                        "pnl": resultado.get("pnl", 0)
                    }
                    emit_dc_event("dc_module_complete", "TP_STOP", "erro",
                    ticker=ticker, descricao=f"TP/STOP atingido: {resultado.get('motivo', '')}")
                    emit_log(f"[DAILY] {ticker}: {resultado['motivo']}", level="info")
                    digest[ticker] = ticker_digest
                    continue
                else:
                    ticker_digest["posicao"]["pnl"] = resultado.get("pnl", 0)
                    ticker_digest["posicao"]["tp_stop_status"] = "ok"
                    ticker_digest["posicao"]["xlsx_lido"] = True
                    emit_dc_event("dc_module_complete", "TP_STOP", "ok",
                    ticker=ticker, descricao="Posição OK - mantendo")
            else:
                ticker_digest["posicao"]["tp_stop_status"] = "sem_xlsx"
                ticker_digest["posicao"]["xlsx_lido"] = False
                emit_dc_event("dc_module_complete", "TP_STOP", "erro",
                ticker=ticker, descricao="XLSX não disponível - não foi possível verificar TP/STOP")
                emit_log(f"[DAILY] {ticker}: posição aberta mas XLSX não disponível para verificação", level="warning")
                emit_log(f"[DAILY] {ticker}: posição aberta — mantendo", level="info")
            digest[ticker] = ticker_digest
            _atualizar_ativo_store(ticker)
            continue

        ticker_digest["posicao"] = {"aberta": False, "acao": "sem_posicao"}

        # 6. gate_eod (só se OPERAR sem posição)
        try:
            gate_result = await dc_gate_eod(ticker)
            gate_output = gate_result.get("output", "")
            if "OPERAR" in gate_output:
                ticker_digest["gate_eod"] = "OPERAR"
                emit_log(f"[DAILY] {ticker}: gate_eod = OPERAR", level="info")
            elif "MONITORAR" in gate_output:
                ticker_digest["gate_eod"] = "MONITORAR"
                emit_log(f"[DAILY] {ticker}: gate_eod = MONITORAR", level="info")
            else:
                ticker_digest["gate_eod"] = gate_output.strip()
        except Exception as e:
            ticker_digest["gate_eod"] = f"erro: {str(e)}"
            emit_log(f"[DAILY] {ticker}: gate_eod erro — {e}", level="error")

        # Se gate_eod = OPERAR → sinaliza abertura
        if ticker_digest.get("gate_eod") == "OPERAR":
            emit_log(f"[DAILY] {ticker}: gate_eod = OPERAR → sinalizando abertura", level="info")
            # Não pular, apenas registrar
        else:
            emit_log(f"[DAILY] {ticker}: gate_eod = {ticker_digest['gate_eod']} → registrando motivo", level="info")

        digest[ticker] = ticker_digest

        # #3 FIX: Emitir evento quando cada ativo termina - permite atualizar UI durante ciclo
        emit_dc_event("daily_ativo_complete", "DAILY", "ok",
        ticker=ticker, digest=ticker_digest)

    emit_log(f"[DAILY] ✅ Ciclo de manutenção concluído — {len(tickers)} ativos processados", level="info")

    # ═══ NOVO: Retornar digest + eventos críticos para fallback na API ═══
    return {
        "digest": digest,
        "eventos": _eventos_criticos
    }
# ═══ FIM NOVO ═══


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
        modulo=None # EOD não é um módulo principal do fluxo TAPE→ORBIT→FIRE
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
        modulo=None # TUNE é configuração, não módulo do fluxo principal
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

async def dc_reflect_cycle(ticker: str) -> dict:
    """
    Executa reflect_cycle_calcular para o ativo.
    """
    script = _get_dc_script()
    return await _stream_subprocess(
        args=["-m", "delta_chaos.edge", "--modo", "orbit_update", "--ticker", ticker],
        cwd=script.parent,
        action_name="dc_reflect_cycle",
        action_payload={"ticker": ticker},
        modulo="REFLECT"
    )