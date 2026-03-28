from pydantic import BaseModel, Field, ConfigDict, ValidationError
from typing import Optional, Dict, List

# ── Schema legado (para config_manager.py) ──────────────────────
class AssetConfig(BaseModel):
    take_profit: float = Field(..., gt=0, lt=1)
    stop_loss: float = Field(..., gt=0)
    regime_estrategia: Dict[str, Optional[str]]

class ConfigSchema(BaseModel):
    ativos: Dict[str, AssetConfig]

def validate_config(data: dict) -> dict:
    """
    Valida o config completo contra o schema.
    Lança ValidationError (Pydantic) se inválido.
    Retorna o dict original se válido.
    """
    ConfigSchema(**data)
    return data

# ── Nova classe para endpoints /ativos (SPEC-ATLAS-INT-01) ─────
class ATLASEditableFields(BaseModel):
    """
    Campos que o ATLAS pode editar via POST /ativos/{ticker}/update.
    extra='allow' preserva campos do Delta Chaos fora do escopo do ATLAS.
    """
    model_config = ConfigDict(extra='allow')
    take_profit: float = Field(..., gt=0, lt=1)
    stop_loss: float = Field(..., gt=0)
    regime_estrategia: Dict[str, Optional[str]]
    anos_validos: List[int]
 

class PosicaoAberta(BaseModel):
    id: int
    ativo: str
    estrategia: str
    tipo_vol: str  # short vol / long vol / neutro
    horizonte: str  # ciclo / estrutural
    data_entrada: str
    dte: int
    regime_entrada: str
    ir_esperado: float
    ic95_lower: float
    ic95_upper: float
    tp: float
    stop: float
    pnl: float
    delta: float = 0.0

class BookSchema(BaseModel):
    posicoes_abertas: List[PosicaoAberta] = []
    trades: List[Dict] = []
    pnl_total: float = 0.0
    delta_liquido: float = 0.0
    cobertura_put_itm: float = 0.0  # 0-100%