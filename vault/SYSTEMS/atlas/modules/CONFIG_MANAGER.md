---
uid: mod-atlas-006
version: 1.0
status: validated
owner: Chan

function: Validação, sanitarização, escrita atômica e versionamento de configurações submetidas por rotas da API.
file: atlas_backend/core/config_manager.py, atlas_backend/core/config_diff.py, atlas_backend/core/versioning.py
role: Mutador de configuração — único modo permissível de alteração não transacional no config (delta_chaos_config.json, versões etc).

input:
  - ticker: str
  - new_data: dict — dados JSON alterados no frontend.

output:
  - version object: dict com o snapshot + current file gravado atomicamente no disco.

depends_on:

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/API_ROUTES]]

intent:
  - Garantir durabilidade de alterações de board, auditoria obrigatória, versionamento para rollbacks em alterações vitais e validação contra schema JSON.

constraints:
  - Escrita no CONFIG_PATH usa padrão de `tempfile` persistido seguido de file replacement system nativo do Python (os.replace) para escrita transacional.
  - APENAS os campos chaves ("take_profit", "stop_loss", "regime_estrategia", "anos_validos") são listados como editáveis na mutation `update_config`.

notes:
  - Dispara `log_action` do audit logger em toda transação final.
---
