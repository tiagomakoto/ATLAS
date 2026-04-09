# atlas_backend/core/event_bus.py
import asyncio
from asyncio import Queue
from datetime import datetime
from typing import Optional
import os

event_queue: Queue = Queue()

# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE EVENTOS DO DELTA CHAOS
# ─────────────────────────────────────────────────────────────────────────────
# Estes eventos são emitidos pelos módulos do Delta Chaos (TAPE, ORBIT, FIRE,
# GATE, REFLECT) e processados pelo frontend para mostrar status em tempo real.
#
# Formato do evento:
#   {
#     "type": "dc_module_start" | "dc_module_complete" | "dc_module_progress" | "dc_module_error" | "dc_workflow_complete",
#     "data": {
#       "modulo": "TAPE" | "ORBIT" | "FIRE" | "GATE" | "REFLECT",
#       "status": "running" | "ok" | "error",
#       "progress": 0-100,  # opcional
#       "timestamp": ISO8601,
#       ...metadata adicional
#     }
#   }
#
# COMENTÁRIO CRÍTICO — NÃO REMOVER. Essa estrutura é a base para comunicação
# entre backend e frontend, substituindo o parsing frágil de texto dos logs.
# ─────────────────────────────────────────────────────────────────────────────

DC_MODULE_NAMES = {"TAPE", "ORBIT", "FIRE", "GATE", "REFLECT"}

DC_EVENT_TYPES = {
    "dc_module_start": "Início de execução de um módulo",
    "dc_module_complete": "Conclusão de módulo com status (ok/error)",
    "dc_module_progress": "Progresso percentual de módulo (0-100)",
    "dc_module_error": "Erro fatal em módulo",
    "dc_workflow_complete": "Workflow completo (todas as etapas finalizadas)",
}


def emit_dc_event(event_type: str, modulo: str, status: Optional[str] = None, **metadata) -> None:
    """
    Emite evento estruturado do Delta Chaos para o sistema de eventos.

    Args:
        event_type: Um dos DC_EVENT_TYPES (dc_module_start, dc_module_complete, etc.)
        modulo: Nome do módulo ("TAPE", "ORBIT", "FIRE", "GATE", "REFLECT")
        status: Status do módulo ("running", "ok", "error")
        **metadata: Campos adicionais (progress, ticker, anos, etc.)

    Exemplo:
        emit_dc_event("dc_module_complete", "ORBIT", "ok", ticker="PETR4")
    """
    # Gerar message amigável para display
    if event_type == "dc_module_start":
        message = f"{modulo} iniciado"
    elif event_type == "dc_module_complete":
        message = f"{modulo} {'ok' if status == 'ok' else 'falhou'}"
    elif event_type == "dc_module_error":
        message = f"{modulo} erro"
    else:
        message = f"{modulo}: {event_type}"

    data = {
        "modulo": modulo,
        "status": status,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        **metadata
    }

    # Adiciona progress padrão se não fornecido
    if "progress" not in metadata and event_type == "dc_module_progress":
        data["progress"] = 0

    event = {
        "type": event_type,
        "data": data
    }

    # ── Debug: log do evento emitido ──
    import json
    data_str = json.dumps(data, default=str) if isinstance(data, dict) else str(data)
    if len(data_str) > 500:
        data_str = data_str[:500] + "...(truncated)"
    print(f"[DC-EVENT] type={event_type} | modulo={modulo} | status={status} | data={data_str}")

    emit_event(event)

async def publish_event(event: dict):
    await event_queue.put(event)

def emit_event(event: dict):
    """Compatível com contexto síncrono e assíncrono."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(publish_event(event))
    except RuntimeError:
        asyncio.run(publish_event(event))

async def health_monitor():
    """
    Monitora saúde dos módulos e envia eventos via WebSocket COM health_reason.
    """
    from atlas_backend.api.websocket.stream import manager
    from atlas_backend.core.paths import get_paths
    
    while True:
        try:
            warnings = []
            errors = []
            paths = get_paths()
            
            # Verificar BOOK
            try:
                book_path = os.path.join(paths["book_dir"], "book_paper.json")
                if os.path.exists(book_path):
                    mtime = datetime.fromtimestamp(os.path.getmtime(book_path))
                    age_hours = (datetime.utcnow() - mtime).total_seconds() / 3600
                    if age_hours > 24:
                        warnings.append(f"BOOK: dados desatualizados há {age_hours:.1f}h")
                else:
                    warnings.append("BOOK: arquivo não encontrado")
            except Exception as e:
                errors.append(f"BOOK: erro - {str(e)}")
            
            # Verificar ativos
            try:
                from core.delta_chaos_reader import list_ativos
                ativos = list_ativos()
                if len(ativos) == 0:
                    warnings.append("TAPE: nenhum ativo parametrizado")
            except Exception as e:
                errors.append(f"TAPE: erro - {str(e)}")
            
            # Determinar status
            if errors:
                health_status = "error"
                health_reason = " | ".join(errors)
            elif warnings:
                health_status = "warning"
                health_reason = " | ".join(warnings)
            else:
                health_status = "ok"
                health_reason = ""
            
            # ENVIAR EVENTO VIA WEBSOCKET
            event = {
                "type": "health_update",
                "data": {
                    "health": health_status,
                    "health_reason": health_reason,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            await manager.broadcast(event)
            
        except Exception as e:
            print(f"❌ Erro health_monitor: {e}")
        
        await asyncio.sleep(10)

async def event_dispatcher():
    """
    Loop central que envia eventos para os WebSockets.
    Inclui health_monitor integrado.
    """
    from atlas_backend.api.websocket.stream import manager
    
    # ✅ Iniciar health_monitor em paralelo
    asyncio.create_task(health_monitor())
    
    while True:
        event = await event_queue.get()
        await manager.broadcast(event)