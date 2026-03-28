from core.watchdog import enforce_memory_limit
from core.audit_logger import log_action

def check_process_health():
    try:
        enforce_memory_limit()
    except MemoryError as e:
        log_action(
            action="process_memory_exceeded",
            payload={},
            response={"error": str(e)}
        )
        raise