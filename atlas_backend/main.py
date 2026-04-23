# atlas_backend/main.py
import sys, os
import asyncio
sys.path.insert(0, os.path.dirname(__file__))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import asyncio

from atlas_backend.api.routes import config, modules, mode, ativos, cycle, config_diff, delta_chaos
from atlas_backend.api.websocket.stream import manager
from atlas_backend.core.event_bus import event_dispatcher, set_main_loop
from atlas_backend.core.runtime_mode import get_mode

# ── Variáveis globais ─────────────────────────────────────────────
_started_at = datetime.utcnow()

# ── lifespan ──────────────────────────────────────────────────────
def _sanitize_stale_calibracoes():
    """
    Ao iniciar o servidor, marca como 'paused' qualquer step de calibração
    que ficou com status 'running' de uma execução anterior (processo morto).
    Evita que o drawer reabra mostrando estado 'EXECUTANDO' fantasma.
    """
    import json, os
    from atlas_backend.core.paths import get_paths
    try:
        paths = get_paths()
        config_dir = paths.get("config_dir", "")
        if not os.path.isdir(config_dir):
            return
        for fname in os.listdir(config_dir):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(config_dir, fname)
            try:
                with open(fpath, encoding="utf-8") as f:
                    dados = json.load(f)
                calibracao = dados.get("calibracao")
                if not calibracao:
                    continue
                steps = calibracao.get("steps", {})
                alterado = False
                for step_info in steps.values():
                    if isinstance(step_info, dict) and step_info.get("status") == "running":
                        step_info["status"] = "paused"
                        alterado = True
                if alterado:
                    dados["calibracao"] = calibracao
                    tmp = fpath + ".tmp"
                    with open(tmp, "w", encoding="utf-8") as f:
                        json.dump(dados, f, indent=2, ensure_ascii=False)
                    os.replace(tmp, fpath)
            except Exception:
                pass
    except Exception:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    _sanitize_stale_calibracoes()
    set_main_loop(asyncio.get_running_loop())
    asyncio.create_task(event_dispatcher())
    yield

# ── App ───────────────────────────────────────────────────────────
app = FastAPI(title="ATLAS Backend", lifespan=lifespan)

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

# ── WebSocket /ws/events (único endpoint para todos os eventos) ───
@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket):
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