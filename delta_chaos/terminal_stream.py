# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# DELTA CHAOS â€” atlas_backend/core/terminal_stream.py
# Roteamento de logs para WebSocket /ws/logs
# Fallback: print() quando WebSocket nÃ£o disponÃ­vel
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

import json
import asyncio
import json
from datetime import datetime
from typing import Optional, Set

# Set de conexÃµes WebSocket ativas â€” gerenciado pelo router
_ws_connections: Set = set()


def register_ws(ws) -> None:
    """Registra uma conexÃ£o WebSocket ativa."""
    _ws_connections.add(ws)


def unregister_ws(ws) -> None:
    """Remove uma conexÃ£o WebSocket ao desconectar."""
    _ws_connections.discard(ws)


def emit_log(msg: str, level: str = "info") -> None:
    """
    Emite log para todos os WebSockets conectados.
    Fallback: print() se nenhum WebSocket ativo.
    """
    payload = json.dumps({
        "ts":    datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "msg":   msg,
    })

    if not _ws_connections:
        print(f"[{level.upper()}] {msg}")
        return

    dead = set()
    for ws in _ws_connections:
        try:
            # Tenta enviar â€” se o loop estiver rodando, agenda coroutine
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(ws.send_text(payload))
            else:
                loop.run_until_complete(ws.send_text(payload))
        except Exception:
            dead.add(ws)

    for ws in dead:
        _ws_connections.discard(ws)


def emit_error(e: Exception) -> None:
    """Emite log de erro."""
    emit_log(str(e), level="error")


class StreamCapture:
    """
    Redireciona sys.stdout para emit_log durante execuÃ§Ã£o de endpoints.

    Uso:
        old_stdout = sys.stdout
        sys.stdout = StreamCapture()
        try:
            resultado = edge.executar_eod(...)
        finally:
            sys.stdout = old_stdout
    """
    def write(self, text: str) -> None:
        if text.strip():
            emit_log(text.strip(), level="info")

    def flush(self) -> None:
        pass
