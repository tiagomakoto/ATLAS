# atlas_backend/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import asyncio

from atlas_backend.api.routes import config, modules, mode, ativos, cycle, config_diff, delta_chaos
from atlas_backend.api.websocket.stream import manager
from atlas_backend.core.event_bus import event_dispatcher
from atlas_backend.core.runtime_mode import get_mode
from atlas_backend.core.terminal_stream import emit_log, emit_error, set_ws_broadcast

# ── Variáveis globais ─────────────────────────────────────────────
_started_at = datetime.utcnow()
_ws_connections: list[WebSocket] = []

# ── lifespan ──────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(event_dispatcher())
    yield

# ── App ───────────────────────────────────────────────────────────
app = FastAPI(title="ATLAS Backend", lifespan=lifespan)

# ── WebSocket /ws/logs (SEM heartbeat customizado) ────────────────
@app.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket):
    await websocket.accept()
    _ws_connections.append(websocket)
    
    # Log via broadcast (chega no cliente WebSocket)
    emit_log(f"WebSocket client conectado — total: {len(_ws_connections)}")
    
    try:
        # Mantém conexão aberta; biblioteca websockets gerencia ping/pong nativamente
        while True:
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if websocket in _ws_connections:
            _ws_connections.remove(websocket)

async def broadcast_to_logs(message: str, level: str = "info"):
    """Broadcast seguro para todos os clientes conectados."""
    for ws in _ws_connections[:]:
        try:
            await ws.send_json({"type": "terminal_log", "level": level, "message": message})
        except Exception:
            if ws in _ws_connections:
                _ws_connections.remove(ws)

# ── REGISTRA broadcast ───────────────────────────────────────────
set_ws_broadcast(broadcast_to_logs)

# ── Routers ───────────────────────────────────────────────────────
app.include_router(delta_chaos.router)
app.include_router(config.router)
app.include_router(modules.router)
app.include_router(config_diff.router)
app.include_router(mode.router)
app.include_router(ativos.router)
app.include_router(cycle.router)

# ── Middleware ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health check ──────────────────────────────────────────────────
@app.get("/")
def health_check():
    now = datetime.utcnow()
    uptime = int((now - _started_at).total_seconds())
    return {
        "status": "ok",
        "system": "ATLAS Backend",
        "mode": get_mode(),
        "uptime_seconds": uptime,
        "timestamp": now.isoformat(),
    }

# ── Outros WebSockets (manager) ───────────────────────────────────
@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.websocket("/ws/modules")
async def ws_modules(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ── Endpoints de teste ────────────────────────────────────────────
@app.get("/cycle")
async def get_cycle():
    return {
        "ativo": "VALE3",
        "regime": "NEUTRO_TRANSICAO",
        "confianca": 0.72,
        "posicao": "OFF",
        "pnl": 1.016
    }

@app.get("/reading")
async def get_reading():
    return {
        "health": "ok",
        "regime": "bullish",
        "signal": "hold",
        "timestamp": datetime.utcnow().isoformat()
    }