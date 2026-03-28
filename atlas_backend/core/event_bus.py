# atlas_backend/core/event_bus.py
import asyncio
from asyncio import Queue
from datetime import datetime
import os

event_queue: Queue = Queue()

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
    from api.websocket.stream import manager
    from core.paths import get_paths
    
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
    from api.websocket.stream import manager
    
    # ✅ Iniciar health_monitor em paralelo
    asyncio.create_task(health_monitor())
    
    while True:
        event = await event_queue.get()
        await manager.broadcast(event)