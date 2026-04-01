import traceback
from .event_bus import emit_event
from core.audit_logger import log_action


def emit_log(message: str, level: str = "info"):
    event = {
        "type": "terminal_log",
        "level": level,
        "message": message
    }

    emit_event(event)

    log_action(
        action="terminal_log",
        payload={"level": level, "message": message},
        response={"status": "emitted"}
    )


def emit_error(e: Exception):
    tb = traceback.format_exc()

    event = {
        "type": "terminal_error",
        "error": str(e),
        "traceback": tb
    }

    emit_event(event)

    log_action(
        action="terminal_error",
        payload={"error": str(e), "traceback": tb},
        response={"status": "emitted"}
    )