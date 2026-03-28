import asyncio
from core.backup import run_backup
from core.watchdog import load_limits

async def backup_loop():
    limits = load_limits()
    interval = limits.get("backup_interval_seconds", 60)

    while True:
        await asyncio.sleep(interval)

        try:
            run_backup()
        except RuntimeError as e:
            print(f"[BACKUP] Falha: {e}")