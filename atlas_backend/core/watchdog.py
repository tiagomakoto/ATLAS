import json
import os
from pathlib import Path

SYSTEM_CONFIG_PATH = Path("config/system_config.json")

_DEFAULTS = {
    "memory_limit_mb": 512,
    "health_staleness_minutes": 10,
    "backup_interval_seconds": 60,
}


def load_limits() -> dict:
    """
    Carrega limites operacionais do system_config.json.
    Retorna defaults se o arquivo nao existir.
    """
    if not SYSTEM_CONFIG_PATH.exists():
        return dict(_DEFAULTS)

    with open(SYSTEM_CONFIG_PATH) as f:
        data = json.load(f)

    return {**_DEFAULTS, **data}


def enforce_memory_limit():
    """
    Verifica uso de memoria do processo atual.
    Lanca MemoryError se ultrapassar o limite configurado.
    """
    limits = load_limits()
    limit_mb = limits.get("memory_limit_mb", 512)

    try:
        with open(f"/proc/{os.getpid()}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    rss_kb = int(line.split()[1])
                    rss_mb = rss_kb / 1024
                    if rss_mb > limit_mb:
                        raise MemoryError(
                            f"Uso de memoria {rss_mb:.1f}MB excede limite de {limit_mb}MB"
                        )
                    return
    except FileNotFoundError:
        pass  # nao-Linux: ignora silenciosamente
