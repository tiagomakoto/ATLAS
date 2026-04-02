# atlas_backend/main.py — WebSocket Handler CORIGIDO
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

# ── WebSocket /ws/logs (SEM heartbeat customizado!) ───────────────
@app.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket):
    await websocket.accept()
    _ws_connections.append(websocket)
    client_id = id(websocket)
    print(f"[WS] Client {client_id} conectado. Total: {len(_ws_connections)}")
    
    emit_log(f"WebSocket client conectado — total: {len(_ws_connections)}")
    
    try:
        # ⚠️ SEM heartbeat — biblioteca websockets gerencia ping/pong nativamente
        # Apenas mantém conexão aberta aguardando desconexão do cliente
        while True:
            await asyncio.sleep(60)  # Stay alive, SEM send_json
    except WebSocketDisconnect:
        print(f"[WS] Client {client_id} desconectou")
    except Exception as e:
        print(f"[WS] Client {client_id} erro: {type(e).__name__}: {e}")
    finally:
        # Cleanup garantido
        if websocket in _ws_connections:
            _ws_connections.remove(websocket)
        print(f"[WS] Client {client_id} removido. Total: {len(_ws_connections)}")

async def broadcast_to_logs(message: str, level: str = "info"):
    print(f"[WS BROADCAST] {level}: {message[:60]}...")  # ← DEBUG
    print(f"[WS BROADCAST] Conexões ativas: {len(_ws_connections)}")  # ← DEBUG
    
    for ws in _ws_connections[:]:
        try:
            await ws.send_json({"type": "terminal_log", "level": level, "message": message})
            print(f"[WS BROADCAST] ✓ Enviado")  # ← DEBUG
        except Exception as e:
            print(f"[WS BROADCAST] ✗ Falha: {type(e).__name__}: {e}")  # ← DEBUG
            if ws in _ws_connections:
                _ws_connections.remove(ws)

# ── REGISTRA broadcast (APÓS a definição de broadcast_to_logs!) ───
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