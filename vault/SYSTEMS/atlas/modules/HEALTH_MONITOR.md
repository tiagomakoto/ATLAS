---
uid: mod-atlas-007
version: 1.0
status: validated
owner: Chan

function: Motor de cálculo e monitoramento estrito de health global baseado na cadência do ciclo, processo em background watchdog e gatekeeper.
file: atlas_backend/core/health_monitor.py, atlas_backend/core/watchdog.py, atlas_backend/core/process_guard.py
role: Cão de fila — monitora estagnação ou alertas vermelhos globais na pipeline.

input:
  - check events manuais
  - limites globais (via watchdog) 

output:
  - `health_state` ("green", "yellow", "red")

depends_on:
  - [[SYSTEMS/atlas/modules/EVENT_BUS]]

depends_on_condition:

used_by:

intent:
  - Prevenir encadeamento de falhas e garantir que a stack entre em stand-by sinalizando YELLOW/RED para frontend caso processos fiquem estagnados ou ciclos apontem anomalias.

constraints:
  - Timeout state baseia-se num delta_time em oposição ao last_update timestamp, usando de default 10min limit para amarelamento de state ("health_staleness_minutes").
  
notes:
---
