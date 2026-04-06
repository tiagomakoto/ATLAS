# atlas_backend/core/dc_runner.py
"""
Executor de subprocessos do Delta Chaos.
Único ponto de integração entre ATLAS e Delta Chaos.

EVENTOS ESTRUTURADOS:
  O dc_runner parseia o stdout do subprocesso para detectar transições de
  módulo (TAPE → ORBIT → FIRE) e emite eventos dc_module_start/complete
  a partir do processo uvicorn (onde a event_queue realmente existe).

  Sem isso, os emit_dc_event() chamados dentro do subprocesso vão para o nada,
  pois cada processo Python tem sua própria cópia do event_bus.
"""

import asyncio
import re
import sys
from pathlib import Path
from typing import AsyncIterator, Optional

from atlas_backend.core.paths import get_paths
from atlas_backend.core.terminal_stream import emit_log, emit_error
from atlas_backend.core.audit_logger import log_action
from atlas_backend.core.event_bus import emit_dc_event

# Controle de concorrência global
_dc_running: bool = False

# ── Marcadores de módulo no stdout do subprocesso ──
_MODULE_START_MARKERS = {
    "TAPE":  re.compile(r"\[\s*1\s*/\s*3\s*\]\s*TAPE"),
    "ORBIT": re.compile(r"\[\s*2\s*/\s*3\s*\]\s*ORBIT"),
    "FIRE":  re.compile(r"\[\s*3\s*/\s*3\s*\]\s*FIRE"),
}

_MODULE_COMPLETE_MARKERS = {
    "TAPE":  re.compile(r"Conclu.*do:.*registros|\[\s*2\s*/\s*3\s*\]\s*ORBIT"),
    "ORBIT": re.compile(r"\[\s*3\s*/\s*3\s*\]\s*FIRE"),
    "FIRE":  re.compile(r"EDGE\.backtest conclu.*do"),
}

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
    global _dc_running
    if _dc_running:
        raise RuntimeError("CONFLICT: A engine do Delta Chaos já está em execução no server.")
    
    _dc_running = True
    full_output = []

    # ── Emitir evento de início do módulo ──
    if modulo:
        emit_dc_event("dc_module_start", modulo, "running", **action_payload)

    main_loop = asyncio.get_running_loop()

    # Estado para rastrear módulos detectados no stdout
    detected_modules = {}  # modulo -> {"started": bool, "completed": bool}

    def _check_module_transitions(line: str):
        """Verifica se a linha indica início ou conclusão de um módulo."""
        for mod_name, pattern in _MODULE_START_MARKERS.items():
            if pattern.search(line):
                if mod_name not in detected_modules:
                    detected_modules[mod_name] = {"started": True, "completed": False}
                    emit_dc_event("dc_module_start", mod_name, "running", **action_payload)

        for mod_name, pattern in _MODULE_COMPLETE_MARKERS.items():
            if pattern.search(line):
                if mod_name not in detected_modules:
                    detected_modules[mod_name] = {"started": True, "completed": True}
                else:
                    detected_modules[mod_name]["completed"] = True
                emit_dc_event("dc_module_complete", mod_name, "ok", **action_payload)

    def _sync_runner():
        import subprocess
        import os

        env = os.environ.copy()
        # Garante que o python vai enxergar a raiz do ATLAS como import root pra rodar o module 'delta_chaos'
        env["PYTHONPATH"] = str(cwd.parent)
        # Força o Windows a renderizar prints com UTF-8 nativamente para as setas e cores do terminal não crasharem
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

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

            # ── Detectar transições de módulo no stdout ──
            _check_module_transitions(line)

            lvl = "info"
            if line.startswith("ERRO") or line.startswith("✗") or "Error" in line:
                lvl = "error"
            elif line.startswith("⚠") or line.startswith("~"):
                lvl = "warning"
            
            main_loop.call_soon_threadsafe(emit_log, line, lvl)

        proc.wait()
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
        
        # ── Marcar módulos detectados mas não concluídos como erro ──
        if status == "ERRO":
            for mod_name, mod_state in detected_modules.items():
                if not mod_state.get("completed", False):
                    emit_dc_event("dc_module_complete", mod_name, "error", **action_payload)
        
        if tem_erro and returncode == 0:
            emit_log("[ORQUESTRADOR] ⚠ Processo completou mas com warnings", level="warning")

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
    finally:
        _dc_running = False

def _validar_caminho(caminho: str) -> None:
    paths = get_paths()
    base = Path(paths.get("delta_chaos_base", ""))
    try:
        Path(caminho).resolve().relative_to(base.resolve())
    except ValueError:
        raise ValueError(f"CRÍTICO: Caminho de arquivo tenta escapar do root base directory: {base}")


async def run_eod_preview(xlsx_dir: str) -> dict:
    _validar_caminho(xlsx_dir)
    script = _get_dc_script()
    return await _stream_subprocess(
        args=["-m", "delta_chaos.edge", "--modo", "eod_preview", "--xlsx_dir", xlsx_dir],
        cwd=script.parent,
        action_name="dc_eod_preview",
        action_payload={"xlsx_dir": xlsx_dir},
        modulo=None  # EOD preview não é um módulo principal
    )

async def run_eod(xlsx_dir: str) -> dict:
    _validar_caminho(xlsx_dir)
    script = _get_dc_script()
    return await _stream_subprocess(
        args=["-m", "delta_chaos.edge", "--modo", "eod", "--xlsx_dir", xlsx_dir],
        cwd=script.parent,
        action_name="dc_eod_executar",
        action_payload={"xlsx_dir": xlsx_dir},
        modulo=None  # EOD não é um módulo principal do fluxo TAPE→ORBIT→FIRE
    )

async def run_orbit(ticker: str, anos: Optional[list] = None) -> dict:
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

async def run_tune(ticker: str) -> dict:
    script = _get_dc_script()
    return await _stream_subprocess(
        args=["-m", "delta_chaos.edge", "--modo", "tune", "--ticker", ticker],
        cwd=script.parent,
        action_name="dc_tune",
        action_payload={"ticker": ticker},
        modulo=None  # TUNE é configuração, não módulo do fluxo principal
    )

async def run_gate(ticker: str) -> dict:
    script = _get_dc_script()
    return await _stream_subprocess(
        args=["-m", "delta_chaos.edge", "--modo", "backtest_gate", "--ticker", ticker],
        cwd=script.parent,
        action_name="dc_gate",
        action_payload={"ticker": ticker},
        modulo="GATE"
    )

async def run_backtest_gate(ticker: str) -> dict:
    """Executa GATE via backtest completo (8 etapas) para atualização mensal."""
    script = _get_dc_script()
    return await _stream_subprocess(
        args=["-m", "delta_chaos.edge", "--modo", "backtest_gate", "--ticker", ticker],
        cwd=script.parent,
        action_name="dc_backtest_gate",
        action_payload={"ticker": ticker},
        modulo="GATE"
    )

async def run_reflect(ticker: str) -> dict:
    """DEPRECATED — usar run_reflect_daily ou run_orbit_update."""
    raise NotImplementedError(
        "run_reflect foi descontinuado. "
        "Use run_reflect_daily(ticker, xlsx_path) para EOD diário "
        "ou run_orbit_update(ticker) para atualização mensal."
    )

async def run_orbit_update(ticker: str, anos: Optional[list] = None) -> dict:
    script = _get_dc_script()
    args = ["-m", "delta_chaos.edge", "--modo", "orbit", "--ticker", ticker]
    if anos:
        args += ["--anos", ",".join(str(a) for a in anos)]
    return await _stream_subprocess(
        args=args,
        cwd=script.parent,
        action_name="dc_orbit_update",
        action_payload={"ticker": ticker, "anos": anos}
    )

async def run_reflect_daily(ticker: str, xlsx_path: str) -> dict:
    script = _get_dc_script()
    return await _stream_subprocess(
        args=["-m", "delta_chaos.edge", "--modo", "reflect_daily",
              "--ticker", ticker, "--xlsx_path", xlsx_path],
        cwd=script.parent,
        action_name="dc_reflect_daily",
        action_payload={"ticker": ticker, "xlsx_path": xlsx_path}
    )

async def run_gate_eod(ticker: str) -> dict:
    script = _get_dc_script()
    return await _stream_subprocess(
        args=["-m", "delta_chaos.edge", "--modo", "gate_eod", "--ticker", ticker],
        cwd=script.parent,
        action_name="dc_gate_eod",
        action_payload={"ticker": ticker}
    )
