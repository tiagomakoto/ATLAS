from datetime import datetime
from core.event_bus import emit_event

last_calibration = datetime.utcnow()

def update_calibration():
    global last_calibration
    last_calibration = datetime.utcnow()

def emit_staleness():
    delta = datetime.utcnow() - last_calibration

    emit_event({
        "type": "calibration_staleness",
        "seconds": int(delta.total_seconds())
    })