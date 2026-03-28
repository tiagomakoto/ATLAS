from core.event_bus import emit_event

cycle_state = {
    "ativo": None,
    "regime": None,
    "regime_confianca": None,
    "posicao": False,
    "pnl": 0.0
}

def update_cycle(data: dict):
    cycle_state.update(data)

    event = {
        "type": "cycle_update",
        "data": dict(cycle_state)
    }

    emit_event(event)

    return event