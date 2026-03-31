from fastapi import APIRouter, HTTPException
from core.config_manager import load_config, update_config

router = APIRouter()

@router.post("/config/update")
def update(payload: dict):
    ticker = payload.get("ticker")      # ← EXTRAIR ticker
    
    print(ticker)
    data = payload.get("data")
    description = payload.get("description", "").strip()
    confirm = payload.get("confirm", False)

    if not ticker:
        raise HTTPException(status_code=400, detail={"error": "TICKER_REQUIRED"})
    if not description:
        raise HTTPException(status_code=400, detail={"error": "DESCRIPTION_REQUIRED"})
    if not confirm:
        raise HTTPException(status_code=400, detail={"error": "CONFIRMATION_REQUIRED"})
    if not data:
        raise HTTPException(status_code=400, detail={"error": "DATA_REQUIRED"})

    version = update_config(ticker, data, description)

    return {"status": "OK", "version": version["version_id"]}