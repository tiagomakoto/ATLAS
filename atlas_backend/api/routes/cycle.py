
from fastapi import APIRouter

router = APIRouter()

@router.get("/cycle")
async def get_cycle():
    return {
        "ativo": "BTCUSDT",
        "regime": "trending",
        "confianca": 0.72,
        "posicao": "long",
        "pnl": 123.45
    }

@router.get("/reading")
async def get_reading():
    return {
        "health": "ok",
        "regime": "bullish",
        "signal": "hold",
        "timestamp": "2026-03-27T00:00:00Z"
    }