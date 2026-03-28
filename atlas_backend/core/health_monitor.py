from datetime import datetime, timedelta
from core.watchdog import load_limits
from core.event_bus import emit_event

health_state = "green"

last_cycle_ok = True
gate_ok = True
last_update = datetime.utcnow()

def evaluate_health():
    global health_state

    limits = load_limits()
    staleness_minutes = limits.get("health_staleness_minutes", 10)

    now = datetime.utcnow()

    if not last_cycle_ok or not gate_ok:
        health_state = "red"
    elif (now - last_update) > timedelta(minutes=staleness_minutes):
        health_state = "yellow"
    else:
        health_state = "green"

    return {
        "type": "health",
        "status": health_state
    }

# ✅ alimentação real do estado

def set_cycle_status(ok: bool):
    global last_cycle_ok, last_update
    last_cycle_ok = ok
    last_update = datetime.utcnow()

    emit_event(evaluate_health())

def set_gate_status(ok: bool):
    global gate_ok
    gate_ok = ok

    emit_event(evaluate_health())