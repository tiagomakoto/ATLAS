MODE = "observe"  # observe | live

def is_observe():
    return MODE == "observe"

def require_live():
    if MODE != "live":
        raise RuntimeError("EXECUTION_BLOCKED_OBSERVE_MODE")

def set_mode(mode: str):
    global MODE
    if mode not in ("observe", "live"):
        raise ValueError(f"Modo inválido: {mode}. Aceitos: observe | live")
    MODE = mode
    return MODE

def get_mode():
    return MODE