import sys
import asyncio
import uvicorn

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if __name__ == "__main__":
    print("🚀 Iniciando ATLAS Server com WindowsProactor (Suporte a Subprocessos AsyncHabilitado)")
    uvicorn.run("atlas_backend.main:app", host="0.0.0.0", port=8000, reload=True)
