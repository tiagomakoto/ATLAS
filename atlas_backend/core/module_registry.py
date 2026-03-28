import asyncio
from typing import Dict

MODULES = ["TAPE", "ORBIT", "FIRE", "BOOK", "EDGE", "GATE", "TUNE"]

module_status: Dict[str, str] = {m: "idle" for m in MODULES}
_lock = asyncio.Lock()

async def update_module_async(module: str, status: str):
    async with _lock:
        module_status[module] = status

    return {
        "type": "module_status",
        "module": module,
        "status": status
    }

# wrapper compatível com código existente
def update_module(module: str, status: str):
    try:
        loop = asyncio.get_running_loop()
        return loop.create_task(update_module_async(module, status))
    except RuntimeError:
        return asyncio.run(update_module_async(module, status))

def get_all_modules():
    return dict(module_status)