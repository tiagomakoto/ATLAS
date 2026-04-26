---
uid: mod-atlas-032
version: 1.0
status: validated
owner: Chan
function: Define e valida schemas Pydantic para configuração de ativos, campos editáveis via ATLAS, posições abertas e book — garante tipagem e constraints antes de persistir.
file: atlas_backend/core/schema_validator.py
role: Guardião de schema — valida toda mutação de dados contra contratos Pydantic antes da escrita.
input:
  - data: dict — dados a validar contra ConfigSchema ou ATLASEditableFields
output:
  - validate_config: dict — retorna dados originais se válido, levanta ValidationError se inválido
  - ATLASEditableFields: BaseModel — schema para edição via API
  - PosicaoAberta: BaseModel — schema de posição aberta
  - BookSchema: BaseModel — schema do book de operações
depends_on: []
depends_on_condition: []
used_by:
  - [[SYSTEMS/atlas/modules/CONFIG_MANAGER]]
  - [[SYSTEMS/atlas/modules/API_ROUTES]]
intent:
  - Impedir dados inválidos de entrar no sistema. Dois níveis: ConfigSchema (legacy) e ATLASEditableFields (SPEC-ATLAS-INT-01 com extra='allow').
constraints:
  - AssetConfig: take_profit gt=0 lt=1, stop_loss gt=0
  - ATLASEditableFields: extra='allow' — preserva campos não-ATLAS
  - PosicaoAberta: 15 campos obrigatórios + delta default=0.0
  - BookSchema: listas default=[], floats default=0.0
notes:
  - ATLASEditableFields usa extra='allow' para não descartar campos do Delta Chaos que não estão no schema ATLAS
