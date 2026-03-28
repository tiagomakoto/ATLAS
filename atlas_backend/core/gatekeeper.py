from core.terminal_stream import emit_log

def gate_decision(signal):
    threshold = 0.6
    value = float(signal["confidence"])

    if value < threshold:
        reason = "LOW_CONFIDENCE"

        emit_log(
            f"GATE REJECTED: {reason} | value={value} < threshold={threshold}",
            level="warning"
        )

        return {
            "approved": False,
            "reason": reason,
            "rule": "signal.confidence >= 0.6",
            "value": value,
            "threshold": threshold
        }

    return {
        "approved": True
    }