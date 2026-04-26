---
uid: mod-atlas-031
version: 1.0
status: validated
owner: Chan
function: Fornece todos os caminhos de filesystem do sistema via config/paths.json com fallback para ~/DeltaChaos/ hardcoded.
file: atlas_backend/core/paths.py
role: Fonte única de paths — nenhum outro módulo conhece caminhos absolutos do filesystem.
input: []
output:
  - get_paths: dict — dicionário de caminhos de diretório (delta_chaos_base, config_dir, etc.)
depends_on: []
depends_on_condition: []
used_by:
  - [[SYSTEMS/atlas/modules/ATLAS_DC_RUNNER]]
  - [[SYSTEMS/atlas/modules/DATA_READERS]]
  - [[SYSTEMS/atlas/modules/gate_helper]]
  - [[SYSTEMS/atlas/modules/fire_helper]]
  - [[SYSTEMS/delta_chaos/modules/INIT]]
intent:
  - Centralizar toda a configuração de paths em um único ponto de leitura. Eliminar caminhos hardcoded espalhados pelo sistema.
constraints:
  - Fallback: ~/DeltaChaos/ se paths.json ausente
  - Strip whitespace de keys/values
  - Normaliza / para \ no Windows
  - Arquivo: config/paths.json relativo à raiz do projeto
notes:
  - Compatível com INIT.md do Delta Chaos que lê delta_chaos_base do mesmo paths.json
