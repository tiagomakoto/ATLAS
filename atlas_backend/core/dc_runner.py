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
import re
import sys
import time
from datetime import date, datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import AsyncIterator, Optional
import delta_chaos.edge as edge

from atlas_backend.core.paths import get_paths
from atlas_backend.core.terminal_stream import emit_log, emit_error
from atlas_backend.core.audit_logger import log_action
from atlas_backend.core.event_bus import emit_dc_event
from atlas_backend.core.timeutils import iso_utc

# Controle de concorrência global
_dc_running: bool = False

# ── DEBUG: limitar a um único ativo para testes ──
DEBUG_TICKER = None # None = roda todos

ATLAS_ROOT = Path(__file__).resolve().parent.parent.parent
TMP_DIR = ATLAS_ROOT / "tmp"

def _get_tune_trials_total() -> int:
    """Fonte única para total de trials do TUNE na calibração."""
    try:
        cfg_path = Path(get_paths().get("delta_chaos_base", "")) / "delta_chaos_config.json"
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return int((cfg.get("tune") or {}).get("trials_por_candidato", 150))
    except Exception:
        return 150

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
        if not isinstance(historico_config, list):
            historico_config = []
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
        ticker_digest = {"ticker": ticker, "xlsx": None, "bloco_mensal": None}

        # ═══ NOVO: Verificar se ativo tem historico_config (calibração feita) ═══
        from atlas_backend.core.delta_chaos_reader import get_ativo
        dados = get_ativo(ticker)
        gate_ok = len(dados.get("historico_config", [])) > 0
        if not gate_ok:
            emit_log(f"[DAILY] {ticker}: calibração incompleta — aguardando GATE", level="warning")
            # ═══ NOVO: Emitir evento para frontend mostrar GATE vermelho ═══
            emit_dc_event("dc_module_complete", "GATE_EOD", "error",
                          ticker=ticker, descricao="calibração incompleta — aguardando GATE")
            # ═══ NOVO: Adicionar à lista de eventos críticos para fallback na API ═══
            _eventos_criticos.append({
                "type": "dc_module_complete",
                "data": {
                    "modulo": "GATE",
                    "status": "error",
                    "ticker": ticker,
                    "descricao": "calibração incompleta — aguardando GATE"
                }
            })
            # ═══ FIM NOVO ═══
            # ═══ Item 4: Adicionar gate_eod no digest para ativos bloqueados ═══
            ticker_digest["gate_eod"] = "BLOQUEADO — calibração não realizada"
            ticker_digest["motivo"] = "calibração incompleta — aguardando GATE"
            digest[ticker] = ticker_digest
            _atualizar_ativo_store(ticker)
            emit_dc_event("daily_ativo_complete", "DAILY", "ok",
                          ticker=ticker, digest=ticker_digest)
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
                _atualizar_ativo_store(ticker)
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
                    _atualizar_ativo_store(ticker)
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
                _atualizar_ativo_store(ticker)
                continue

        # Após bloco mensal (se executou), continuar para XLSX
        emit_log(f"[DAILY] {ticker}: continuando para XLSX", level="info")

        # 3. GATE EOD (apenas avaliação, sem bloco mensal)
        try:
            gate_result = await dc_gate_eod(ticker)
            gate_output = gate_result.get("output", "")
            if "BLOQUEADO" in gate_output:
                ticker_digest["gate_eod"] = "BLOQUEADO"
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
            _atualizar_ativo_store(ticker)
            continue

        # 4. XLSX EOD
        xlsx_path = _detectar_xlsx(ticker)
        if xlsx_path:
            emit_log(f"[DAILY] {ticker}: xlsx encontrado, rodando reflect_daily", level="info")
            try:
                await dc_reflect_daily(ticker, xlsx_path)
                emit_dc_event("dc_module_complete", "XLSX", "ok",
                              ticker=ticker, descricao="XLSX EOD encontrado")
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
                    _atualizar_ativo_store(ticker)
                    emit_dc_event("daily_ativo_complete", "DAILY", "ok",
                                  ticker=ticker, digest=ticker_digest)
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
                emit_dc_event("daily_ativo_complete", "DAILY", "ok",
                              ticker=ticker, digest=ticker_digest)
                continue

        ticker_digest["posicao"] = {"aberta": False, "acao": "sem_posicao"}

        # gate_eod já foi avaliado no bloco 3 — resultado em ticker_digest["gate_eod"]
        if ticker_digest.get("gate_eod") == "OPERAR":
            emit_log(f"[DAILY] {ticker}: gate_eod = OPERAR → sinalizando abertura", level="info")
        else:
            emit_log(f"[DAILY] {ticker}: gate_eod = {ticker_digest.get('gate_eod', '—')} → registrando motivo", level="info")

        digest[ticker] = ticker_digest
        _atualizar_ativo_store(ticker)
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
    try:
        await asyncio.to_thread(edge.rodar_backtest_dados, ticker, anos)
        log_action("dc_orbit", action_payload, {"status": "OK"})
        return {"status": "OK", "returncode": 0, "output": ""}
    except Exception as e:
        emit_log(f"[ORBIT] {ticker}: erro — {e}", level="error")
        log_action("dc_orbit", action_payload, {"status": "ERRO", "error": repr(e)})
        return {"status": "ERRO", "output": repr(e)}

async def dc_tune(ticker: str) -> dict:
    action_payload = {"ticker": ticker}
    emit_dc_event("dc_module_start", "TUNE", "running", **action_payload)
    try:
        edge_result = await asyncio.to_thread(edge.rodar_tune, ticker)
        emit_dc_event("dc_module_complete", "TUNE", "ok", **action_payload)
        log_action("dc_tune", action_payload, {"status": "OK"})
        tune_resultado = edge_result.get("resultado", {}) if isinstance(edge_result, dict) else {}
        return {"status": "OK", "returncode": 0, "output": "", "tune_resultado": tune_resultado}
    except Exception as e:
        emit_dc_event("dc_module_complete", "TUNE", "error", **action_payload)
        emit_log(f"[TUNE] {ticker}: erro — {e}", level="error")
        log_action("dc_tune", action_payload, {"status": "ERRO", "error": repr(e)})
        return {"status": "ERRO", "output": repr(e)}

async def dc_gate_backtest(ticker: str) -> dict:
    action_payload = {"ticker": ticker}
    emit_dc_event("dc_module_start", "GATE", "running", **action_payload)
    try:
        res = await asyncio.to_thread(edge.rodar_backtest_gate, ticker)
        gate_resultado = _build_gate_resultado(res.get("gate_data", {}), ticker)
        emit_dc_event("dc_module_complete", "GATE", "ok", gate_resultado=gate_resultado, **action_payload)
        log_action("dc_backtest_gate", action_payload, {"status": "OK"})
        return {"status": "OK", "returncode": 0, "output": res.get("output", ""), "gate_resultado": gate_resultado}
    except Exception as e:
        emit_dc_event("dc_module_complete", "GATE", "error", erro=str(e), **action_payload)
        emit_log(f"[GATE] {ticker}: erro — {e}", level="error")
        log_action("dc_backtest_gate", action_payload, {"status": "ERRO", "error": repr(e)})
        return {"status": "ERRO", "output": repr(e)}

def _build_gate_resultado(gate_data: dict, ticker: str) -> dict:
    gates = gate_data.get("gates", {})
    gate_valores = gate_data.get("gate_valores", {})
    decisao = gate_data.get("decisao", "BLOQUEADO")
    criterios = []
    for nome_completo, passou in gates.items():
        partes = nome_completo.split(" — ", 1)
        criterios.append({
            "id": partes[0].strip(),
            "nome": partes[1].strip() if len(partes) > 1 else partes[0].strip(),
            "passou": bool(passou),
            "valor": gate_valores.get(nome_completo, "N/D"),
        })
    falhas = [c["id"] for c in criterios if not c["passou"]]
    return {
        "ticker": ticker,
        "criterios": criterios,
        "resultado": decisao,
        "falhas": falhas if decisao != "OPERAR" else [],
    }


async def dc_fire_diagnostico(ticker: str) -> dict:
    action_payload = {"ticker": ticker}
    emit_dc_event("dc_module_start", "FIRE", "running", **action_payload)
    try:
        from atlas_backend.core.delta_chaos_reader import get_fire_diagnostico

        diagnostico = await asyncio.to_thread(get_fire_diagnostico, ticker)
        emit_dc_event("dc_module_complete", "FIRE", "ok", fire_diagnostico=diagnostico, **action_payload)
        return {"status": "OK", "fire_diagnostico": diagnostico}
    except Exception as e:
        emit_dc_event("dc_module_complete", "FIRE", "error", erro=str(e), **action_payload)
        emit_log(f"[FIRE] {ticker}: erro â€” {e}", level="error")
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
    try:
        res = await asyncio.to_thread(edge.rodar_gate_eod, ticker)
        log_action("dc_gate_eod", action_payload, {"status": "OK"})
        return {"status": "OK", "returncode": 0, "output": res.get("output", "")}
    except Exception as e:
        emit_log(f"[GATE_EOD] {ticker}: erro — {e}", level="error")
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

async def dc_calibracao_iniciar(ticker: str) -> dict:
    """
    Inicia calibração completa de novo ativo.
    Sequência: backtest_dados → tune → gate + fire
    Cria/atualiza campo calibracao no master JSON, dispara step 1 via subprocess EM BACKGROUND
    """
    # Validação básica do ticker
    import re
    if not re.match(r"^[A-Z0-9]{4,6}$", ticker):
        raise ValueError(f"Ticker inválido: {ticker}")

    # 1. Criar/Atualizar campo calibracao no master JSON
    from atlas_backend.core.delta_chaos_reader import get_ativo, update_ativo
    from atlas_backend.core.paths import get_paths
    from pathlib import Path
    import json
    from datetime import datetime

    # Verificar se ativo existe, criar se necessário
    paths = get_paths()
    config_path = Path(paths["config_dir"]) / f"{ticker}.json"

    if not config_path.exists():
        # Criar ativo com estrutura básica
        dados = {
            "ticker": ticker,
            "status": "MONITORAR",
            "calibracao": {
                "step_atual": 1,
                "steps": {
                    "1_backtest_dados": {"status": "idle", "iniciado_em": None, "concluido_em": None, "erro": None},
                    "2_tune": {"status": "idle", "iniciado_em": None, "concluido_em": None, "erro": None, "trials_completos": 0, "trials_total": _get_tune_trials_total()},
                    "3_gate_fire": {"status": "idle", "iniciado_em": None, "concluido_em": None, "erro": None}
                },
                "ultimo_evento_em": None,
                "gate_resultado": None,
                "fire_diagnostico": None
            },
            "historico": [],
            "historico_config": [],
            "atualizado_em": datetime.now(tz=ZoneInfo('America/Sao_Paulo')).strftime("%Y-%m-%d %H:%M:%S")
        }

        # Criar arquivo
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    else:
        # Carregar dados atuais
        dados = get_ativo(ticker)

    # Inicializar calibracao com estrutura padrão
    calibracao = {
        "step_atual": 1,
        "steps": {
            "1_backtest_dados": {"status": "idle", "iniciado_em": None, "concluido_em": None, "erro": None},
            "2_tune": {"status": "idle", "iniciado_em": None, "concluido_em": None, "erro": None, "trials_completos": 0, "trials_total": _get_tune_trials_total()},
            "3_gate_fire": {"status": "idle", "iniciado_em": None, "concluido_em": None, "erro": None}
        },
        "ultimo_evento_em": None,
        "gate_resultado": None,
        "fire_diagnostico": None
    }

    # Atualizar no master JSON usando versão simplificada
    def _update_ativo_simples(ticker: str, updates: dict):
        """Versão simplificada de update_ativo para calibracao."""
        from atlas_backend.core.paths import get_paths
        import json
        import os
        from datetime import datetime

        paths = get_paths()
        config_path = os.path.join(paths["config_dir"], f"{ticker}.json")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Ativo '{ticker}' não encontrado")

        with open(config_path, 'r', encoding='utf-8') as f:
            current = json.load(f)

        current.update(updates)
        current["atualizado_em"] = datetime.now(tz=ZoneInfo('America/Sao_Paulo')).strftime("%Y-%m-%d %H:%M:%S")

        # Criar arquivo temporário
        tmp_path = config_path + ".tmp"
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(current, f, indent=2, ensure_ascii=False)

        # Substituir arquivo original
        os.replace(tmp_path, config_path)

    _update_ativo_simples(ticker, {"calibracao": calibracao})

    # 2. Disparar step 1 EM BACKGROUND (não bloquear resposta HTTP)
    import asyncio
    asyncio.create_task(_executar_calibracao_step1(ticker))

    # 3. Retornar IMEDIATAMENTE para frontend abrir drawer
    return {"status": "started", "step": 1}

async def _executar_calibracao_step1(ticker: str):
    """Executa step 1 da calibração em background."""
    from atlas_backend.core.delta_chaos_reader import get_ativo
    from datetime import datetime
    import json
    import os

    try:
        def _update_ativo_simples(ticker: str, updates: dict):
            """Versão simplificada de update_ativo para calibracao."""
            from atlas_backend.core.paths import get_paths
            paths = get_paths()
            config_path = os.path.join(paths["config_dir"], f"{ticker}.json")

            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Ativo '{ticker}' não encontrado")

            with open(config_path, 'r', encoding='utf-8') as f:
                current = json.load(f)

            current.update(updates)
            current["atualizado_em"] = datetime.now(tz=ZoneInfo('America/Sao_Paulo')).strftime("%Y-%m-%d %H:%M:%S")

            # Criar arquivo temporário
            tmp_path = config_path + ".tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(current, f, indent=2, ensure_ascii=False)

            # Substituir arquivo original
            os.replace(tmp_path, config_path)

        # 1. Atualizar status para \"running\"
        dados = get_ativo(ticker)
        dados["calibracao"]["steps"]["1_backtest_dados"]["status"] = "running"
        dados["calibracao"]["steps"]["1_backtest_dados"]["iniciado_em"] = iso_utc()
        dados["calibracao"]["ultimo_evento_em"] = iso_utc()
        _update_ativo_simples(ticker, {"calibracao": dados["calibracao"]})

        # 2. Executar backtest
        from atlas_backend.core.dc_runner import dc_orbit_backtest
        result_tune = {"status": "ERRO", "returncode": 1, "output": "Step 1 não concluído"}  # default
        result_gate = {"status": "ERRO", "returncode": 1, "output": "Step 2 não concluído"}  # default
        try:
            result = await dc_orbit_backtest(ticker)
        except Exception as e:
            result = {"status": "ERRO", "returncode": 1, "output": str(e)}

        # 3. Atualizar status para \"done\" ou \"error\"
        dados = get_ativo(ticker)
        if result.get("status") == "OK":
            dados["calibracao"]["steps"]["1_backtest_dados"]["status"] = "done"
        else:
            dados["calibracao"]["steps"]["1_backtest_dados"]["status"] = "error"
            dados["calibracao"]["steps"]["1_backtest_dados"]["erro"] = result.get("output", "Erro desconhecido")

        dados["calibracao"]["steps"]["1_backtest_dados"]["concluido_em"] = iso_utc()
        dados["calibracao"]["ultimo_evento_em"] = iso_utc()
        _update_ativo_simples(ticker, {"calibracao": dados["calibracao"]})

        try:
            # 4. Se step 1 concluído com sucesso, iniciar step 2 automaticamente
            if result.get("status") == "OK":
                # Atualizar step_atual para 2
                dados["calibracao"]["step_atual"] = 2
                dados["calibracao"]["steps"]["2_tune"]["status"] = "running"
                dados["calibracao"]["steps"]["2_tune"]["iniciado_em"] = iso_utc()
                dados["calibracao"]["ultimo_evento_em"] = iso_utc()
                _update_ativo_simples(ticker, {"calibracao": dados["calibracao"]})

                # Executar step 2 (TUNE)
                from atlas_backend.core.dc_runner import dc_tune
                try:
                    result_tune = await dc_tune(ticker)
                except Exception as e:
                    result_tune = {"status": "ERRO", "returncode": 1, "output": str(e)}

                # Atualizar status do step 2
                dados = get_ativo(ticker)
                if result_tune.get("status") == "OK":
                    dados["calibracao"]["steps"]["2_tune"]["status"] = "done"
                else:
                    dados["calibracao"]["steps"]["2_tune"]["status"] = "error"
                    dados["calibracao"]["steps"]["2_tune"]["erro"] = result_tune.get("output", "Erro desconhecido")

                dados["calibracao"]["steps"]["2_tune"]["concluido_em"] = iso_utc()
                dados["calibracao"]["ultimo_evento_em"] = iso_utc()
                _update_ativo_simples(ticker, {"calibracao": dados["calibracao"]})

            # 5. Se step 2 concluído com sucesso, iniciar step 3 automaticamente
            # D8 (TUNE v3.0): pausa antes do step 3 se ainda há regimes elegíveis pendentes de confirmação.
            if result_tune.get("status") == "OK":
                dados = get_ativo(ticker)
                ranking_root = dados.get("tune_ranking_estrategia") or {}
                meta_ranking = ranking_root.get("_meta") or {}
                regimes_pendentes = any(
                    not v.get("confirmado", False)
                    and v.get("eleicao_status") in {"competitiva", "estrutural_fixo"}
                    for k, v in ranking_root.items()
                    if k != "_meta" and isinstance(v, dict)
                ) if meta_ranking.get("concluido_em") else False

                if regimes_pendentes:
                    # Pausar step 3 aguardando confirmação CEO
                    dados["calibracao"]["step_atual"] = 3
                    dados["calibracao"]["steps"]["3_gate_fire"]["status"] = "paused"
                    dados["calibracao"]["steps"]["3_gate_fire"]["iniciado_em"] = iso_utc()
                    dados["calibracao"]["steps"]["3_gate_fire"]["erro"] = "aguardando_confirmacao_regimes"
                    dados["calibracao"]["ultimo_evento_em"] = iso_utc()
                    _update_ativo_simples(ticker, {"calibracao": dados["calibracao"]})
                    emit_dc_event("dc_module_start", "GATE", "paused", ticker=ticker,
                                  motivo="aguardando_confirmacao_regimes")
                    return  # Interrompe — retomado via /retomar após CEO confirmar

                # Atualizar step_atual para 3
                dados["calibracao"]["step_atual"] = 3
                dados["calibracao"]["steps"]["3_gate_fire"]["status"] = "running"
                dados["calibracao"]["steps"]["3_gate_fire"]["iniciado_em"] = iso_utc()
                dados["calibracao"]["ultimo_evento_em"] = iso_utc()
                _update_ativo_simples(ticker, {"calibracao": dados["calibracao"]})

                # Executar step 3 fase A (GATE)
                try:
                    result_gate = await dc_gate_backtest(ticker)
                except Exception as e:
                    result_gate = {"status": "ERRO", "returncode": 1, "output": str(e)}

                # Atualizar status do step 3 (GATE + FIRE)
                dados = get_ativo(ticker)
                if result_gate.get("status") == "OK":
                    dados["calibracao"]["gate_resultado"] = result_gate.get("gate_resultado")
                    gate_aprovado = result_gate.get("gate_resultado", {}).get("resultado") == "OPERAR"
                    if gate_aprovado:
                        result_fire = await dc_fire_diagnostico(ticker)
                        if result_fire.get("status") == "OK":
                            dados["calibracao"]["fire_diagnostico"] = result_fire.get("fire_diagnostico")
                            dados["calibracao"]["steps"]["3_gate_fire"]["status"] = "done"
                        else:
                            dados["calibracao"]["steps"]["3_gate_fire"]["status"] = "error"
                            dados["calibracao"]["steps"]["3_gate_fire"]["erro"] = result_fire.get("output", "Erro desconhecido")
                    else:
                        dados["calibracao"]["steps"]["3_gate_fire"]["status"] = "done"
                else:
                    dados["calibracao"]["steps"]["3_gate_fire"]["status"] = "error"
                    dados["calibracao"]["steps"]["3_gate_fire"]["erro"] = result_gate.get("output", "Erro desconhecido")

                dados["calibracao"]["steps"]["3_gate_fire"]["concluido_em"] = iso_utc()
                dados["calibracao"]["ultimo_evento_em"] = iso_utc()
                _update_ativo_simples(ticker, {"calibracao": dados["calibracao"]})

        except Exception as e:
            # Marcar como erro em caso de exceção
            try:
                dados = get_ativo(ticker)
                step_atual = dados.get("calibracao", {}).get("step_atual", 1)
                modulo = "ORBIT" if step_atual == 1 else "TUNE" if step_atual == 2 else "GATE"
                emit_dc_event("dc_module_complete", modulo, "error", ticker=ticker, erro=str(e))
                
                # Atualizar status do step atual
                step_key = f"{step_atual}_{'backtest_dados' if step_atual == 1 else 'tune' if step_atual == 2 else 'gate_fire'}"
                dados["calibracao"]["steps"][step_key]["status"] = "error"
                dados["calibracao"]["steps"][step_key]["erro"] = str(e)
                dados["calibracao"]["steps"][step_key]["concluido_em"] = iso_utc()

                _update_ativo_simples(ticker, {"calibracao": dados["calibracao"]})
            except:
                pass  # Se falhar, pelo menos tentamos

    except Exception as e:
        # Marcar como erro em caso de exceção
        try:
            dados = get_ativo(ticker)
            step_atual = dados.get("calibracao", {}).get("step_atual", 1)
            modulo = "ORBIT" if step_atual == 1 else "TUNE" if step_atual == 2 else "GATE"
            emit_dc_event("dc_module_complete", modulo, "error", ticker=ticker, erro=str(e))

            # Atualizar status do step atual
            step_key = f"{step_atual}_{'backtest_dados' if step_atual == 1 else 'tune' if step_atual == 2 else 'gate_fire'}"
            dados["calibracao"]["steps"][step_key]["status"] = "error"
            dados["calibracao"]["steps"][step_key]["erro"] = str(e)
            dados["calibracao"]["steps"][step_key]["concluido_em"] = iso_utc()

            _update_ativo_simples(ticker, {"calibracao": dados["calibracao"]})
        except:
            pass  # Se falhar, pelo menos tentamos


async def dc_calibracao_retomar(ticker: str) -> dict:
    """
    Retoma calibração do step atual (usado quando status == "paused")
    Para step 2: Optuna continua do SQLite existente
    """
    # Validação básica do ticker
    import re
    if not re.match(r"^[A-Z0-9]{4,6}$", ticker):
        raise ValueError(f"Ticker inválido: {ticker}")

    from atlas_backend.core.delta_chaos_reader import get_ativo

    # Carregar estado atual
    dados = get_ativo(ticker)
    calibracao = dados.get("calibracao", {})
    step_atual = calibracao.get("step_atual", 1)

    # Verificar se está pausado
    step_key = f"{step_atual}_{'backtest_dados' if step_atual == 1 else 'tune' if step_atual == 2 else 'gate_fire'}"
    if calibracao.get("steps", {}).get(step_key, {}).get("status") != "paused":
        raise ValueError(f"Step {step_atual} não está pausado")

    # Retomar conforme step
    if step_atual == 1:
        # Retomar backtest_dados
        from atlas_backend.core.dc_runner import dc_orbit_backtest
        result = await dc_orbit_backtest(ticker)

        # Atualizar estado
        dados["calibracao"]["steps"][step_key]["status"] = "running"
        dados["calibracao"]["steps"][step_key]["iniciado_em"] = iso_utc()

    elif step_atual == 2:
        # Retomar tune
        from atlas_backend.core.dc_runner import dc_tune
        result = await dc_tune(ticker)

        # Atualizar estado
        dados["calibracao"]["steps"][step_key]["status"] = "running"
        dados["calibracao"]["steps"][step_key]["iniciado_em"] = iso_utc()

    elif step_atual == 3:
        # D8 (TUNE v3.0): rejeitar retomada do step 3 se ainda há regimes pendentes de confirmação
        ranking_root = dados.get("tune_ranking_estrategia") or {}
        meta_ranking = ranking_root.get("_meta") or {}
        regimes_pendentes = any(
            not v.get("confirmado", False)
            and v.get("eleicao_status") in {"competitiva", "estrutural_fixo"}
            for k, v in ranking_root.items()
            if k != "_meta" and isinstance(v, dict)
        ) if meta_ranking.get("concluido_em") else False

        if regimes_pendentes:
            raise ValueError("Confirme todos os regimes elegíveis no ranking TUNE v3.0 antes de iniciar o step 3")

        # Retomar gate + fire
        result = await dc_gate_backtest(ticker)
        if result.get("status") == "OK":
            dados["calibracao"]["gate_resultado"] = result.get("gate_resultado")
            if result.get("gate_resultado", {}).get("resultado") == "OPERAR":
                fire_result = await dc_fire_diagnostico(ticker)
                if fire_result.get("status") == "OK":
                    dados["calibracao"]["fire_diagnostico"] = fire_result.get("fire_diagnostico")

        # Atualizar estado
        dados["calibracao"]["steps"][step_key]["status"] = "running"
        dados["calibracao"]["steps"][step_key]["iniciado_em"] = iso_utc()

    # Atualizar ultimo_evento_em
    dados["calibracao"]["ultimo_evento_em"] = iso_utc()

    # Atualizar no arquivo com escrita atômica
    path_ativo = Path(get_paths()["config_dir"]) / f"{ticker}.json"
    path_tmp = path_ativo.with_suffix(".tmp")

    with open(path_tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
    os.replace(path_tmp, path_ativo)

    return {"status": "resumed", "step": step_atual}


async def dc_calibracao_progresso_tune(ticker: str) -> dict:
    """
    Lê tune_{TICKER}.db via conexão read-only
    Retorna: { "trials_completos": N, "trials_total": <config.tune.trials_por_candidato>, "best_ir": X }
    Conexão deve ser read-only explícita para evitar conflito com processo de escrita
    """
    # Validação básica do ticker
    import re
    if not re.match(r"^[A-Z0-9]{4,6}$", ticker):
        raise ValueError(f"Ticker inválido: {ticker}")

    from pathlib import Path
    import sqlite3

    # Caminho do SQLite
    tmp_dir = Path(__file__).resolve().parent.parent.parent / "tmp"
    db_path = tmp_dir / f"tune_{ticker}.db"

    if not db_path.exists():
        return {"trials_completos": 0, "trials_total": _get_tune_trials_total(), "best_ir": 0.0}

    # Conexão read-only
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cursor = conn.cursor()

        # Contar trials completos
        cursor.execute("SELECT COUNT(*) FROM trial WHERE state = 'COMPLETE'")
        trials_completos = cursor.fetchone()[0]

        # Pegar melhor IR
        cursor.execute("SELECT MAX(value) FROM trial WHERE state = 'COMPLETE'")
        best_ir = cursor.fetchone()[0] or 0.0

        return {
            "trials_completos": trials_completos,
            "trials_total": _get_tune_trials_total(),
            "best_ir": best_ir
        }
    finally:
        conn.close()
