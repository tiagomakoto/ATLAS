# atlas_backend/core/dc_runner.py
"""
Executor de subprocessos do Delta Chaos.
Único ponto de integração entre ATLAS e Delta Chaos.

EVENTOS ESTRUTURADOS:
  Cada função run_* emite eventos dc_module_start e dc_module_complete/error
  via event_bus. O frontend processa esses eventos para mostrar status em
  tempo real (verde/vermelho) sem precisar parsear texto dos logs.
"""

import asyncio
import sys
from pathlib import Path
from typing import AsyncIterator, Optional

from atlas_backend.core.paths import get_paths
from atlas_backend.core.terminal_stream import emit_log, emit_error
from atlas_backend.core.audit_logger import log_action
from atlas_backend.core.event_bus import emit_dc_event

# Controle de concorrência global
_dc_running: bool = False

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
    Executa subprocess do Delta Chaos e emite eventos estruturados.

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
        
        # ── Emitir evento de conclusão do módulo ──
        if modulo:
            dc_status = "ok" if status == "OK" else "error"
            emit_dc_event("dc_module_complete", modulo, dc_status, **action_payload)
        
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
    script = _get_dc_script()
    args = ["-m", "delta_chaos.edge", "--modo", "orbit", "--ticker", ticker]
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
        args=["-m", "delta_chaos.edge", "--modo", "gate", "--ticker", ticker],
        cwd=script.parent,
        action_name="dc_gate",
        action_payload={"ticker": ticker},
        modulo="GATE"
    )

async def run_reflect(ticker: str) -> dict:
    """Executa o módulo Reflect para atualização de dados."""
    script = _get_dc_script()
    return await _stream_subprocess(
        args=["-m", "delta_chaos.edge", "--modo", "reflect", "--ticker", ticker],
        cwd=script.parent,
        action_name="dc_reflect",
        action_payload={"ticker": ticker},
        modulo="REFLECT"
    )
