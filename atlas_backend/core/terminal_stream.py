# atlas_backend/core/terminal_stream.py
"""
Roteamento de logs para WebSocket /ws/events.
Fallback: print() quando WebSocket não disponível.
"""

from .event_bus import emit_event

def emit_log(msg: str, level: str = "info"):
    print(f"[{level.upper()}] {msg}")
    # Emite como evento estruturado para /ws/events
    emit_event({
        "type": "terminal_log",
        "data": {"message": msg, "level": level}
    })

def emit_error(e: Exception):
    print(f"[ERROR] {e}")
    emit_event({
        "type": "terminal_error",
        "data": {"message": str(e), "level": "error"}
    })
