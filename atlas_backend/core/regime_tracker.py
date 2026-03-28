from core.event_bus import emit_event

current_regime = None

def update_regime(new_regime: str, confidence: float):
    global current_regime

    changed = new_regime != current_regime

    current_regime = new_regime

    event = {
        "type": "regime_update",
        "regime": new_regime,
        "confidence": confidence,
        "changed": changed
    }

    emit_event(event)

    # 🔴 ALERTA ATIVO
    if changed:
        emit_event({
            "type": "alert",
            "level": "warning",
            "message": f"Regime mudou para {new_regime}",
            "confidence": confidence
        })