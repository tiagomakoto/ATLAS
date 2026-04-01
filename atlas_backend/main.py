# atlas_backend/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import asyncio
from api.routes import config, modules, mode, ativos, cycle, config_diff
from api.websocket.stream import manager
from core.event_bus import event_dispatcher
from core.runtime_mode import get_mode
from api.routes import delta_chaos
from atlas_backend.api.routes.delta_chaos import router as dc_router





_started_at = datetime.utcnow()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ SÓ chama event_dispatcher (que inicia health_monitor internamente)
    asyncio.create_task(event_dispatcher())
    yield

app = FastAPI(title="ATLAS Backend", lifespan=lifespan)

app.include_router(dc_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config.router)
app.include_router(modules.router)
app.include_router(config_diff.router)
app.include_router(mode.router)
app.include_router(ativos.router)
app.include_router(cycle.router)
app.include_router(delta_chaos.router, prefix="/delta-chaos", tags=["delta-chaos"])

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

@app.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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