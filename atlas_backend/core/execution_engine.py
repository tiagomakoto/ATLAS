from core.runtime_mode import require_live
from core.terminal_stream import emit_log, emit_error
from core.gatekeeper import gate_decision


def execute_order(signal):
    try:
        decision = gate_decision(signal)

        if not decision["approved"]:
            emit_log(f"ORDER BLOCKED: {decision['reason']}", level="warning")
            return

        require_live()

        # execução real aqui
        emit_log("ORDER EXECUTED", level="info")

    except Exception as e:
        emit_error(e)