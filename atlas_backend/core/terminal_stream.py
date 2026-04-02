import traceback
from .event_bus import emit_event
from core.audit_logger import log_action

# broadcast_to_logs será registrado por main.py via set_ws_broadcast()
_ws_broadcast_func = None

def emit_log(msg: str, level: str = "info"):
    print(f"[{level.upper()}] {msg}")
    # Broadcast para WebSocket se disponível
    if _ws_broadcast_func is not None:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(_ws_broadcast_func(msg, level))
            def _check_result(t):
                try:
                    t.result()
                except Exception:
                    pass  # Falha silenciosa
            task.add_done_callback(_check_result)
        except RuntimeError:
            # Sem loop ativo (ex: thread secundária) — ignora silenciosamente
            pass
        except Exception:
            pass  # Falha silenciosa se não houver loop

def emit_error(e: Exception):
    print(f"[ERROR] {e}")
    if _ws_broadcast_func is not None:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_ws_broadcast_func(str(e), "error"))
        except RuntimeError:
            pass
        except Exception:
            pass

def set_ws_broadcast(func):
    """Delta Chaos registra sua função de broadcast aqui."""
    global _ws_broadcast_func
    _ws_broadcast_func = func