---
uid: mod-atlas-038
version: 1.0
status: validated
owner: Chan
function: Registro em memória do status dos 7 módulos Delta Chaos (TAPE, ORBIT, FIRE, BOOK, EDGE, GATE, TUNE) com interface async e sync.
file: atlas_backend/core/module_registry.py
role: Registry de módulos — fonte de verdade para status de cada módulo do pipeline.
input:
  - module: str — nome do módulo
  - status: str — novo status (idle, running, done, error)
output:
  - get_all_modules: dict — {TAPE: idle, ORBIT: idle, ...}
  - update_module_async: dict — evento emitido
depends_on:
  - [[SYSTEMS/atlas/modules/EVENT_BUS]]
depends_on_condition: []
used_by:
  - [[SYSTEMS/atlas/modules/API_ROUTES]]
intent:
  - Prover consulta rápida do status de todos os módulos do pipeline para o frontend via API.
constraints:
  - MODULES = ['TAPE', 'ORBIT', 'FIRE', 'BOOK', 'EDGE', 'GATE', 'TUNE']
  - Status inicial: idle para todos
  - asyncio.Lock para concorrência
  - update_module (sync) usa get_running_loop().create_task() ou asyncio.run() como fallback
notes:
  - REFLECT não está na lista de módulos — vive dentro do TAPE
