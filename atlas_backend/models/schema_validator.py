from pydantic import BaseModel, Field
from typing import Optional, Dict

class AssetConfig(BaseModel):
    take_profit: float = Field(..., gt=0, lt=1)
    stop_loss: float = Field(..., gt=0)
    regime_estrategia: Dict[str, Optional[str]]  # null permitido só onde faz sentido

class ConfigSchema(BaseModel):
    ativos: Dict[str, AssetConfig]