---
uid: mod-atlas-043
version: 1.0
status: validated
owner: Chan
function: Filtro de confiança pré-execução — rejeita sinais com confidence < 0.6 com motivo detalhado e log de warning.
file: atlas_backend/core/gatekeeper.py
role: Porteiro de confiança — primeira barreira programática antes da execução de ordens.
input:
  - signal: dict — sinal de trade com campo confidence (float)
output:
  - gate_decision: dict — {approved: True} ou {approved: False, reason, rule, value, threshold}
depends_on:
  - [[SYSTEMS/atlas/modules/terminal_stream]]
depends_on_condition: []
used_by:
  - [[SYSTEMS/atlas/modules/execution_engine]]
intent:
  - Filtrar sinais de baixa confiança antes que cheguem ao pipeline de execução. Última verificação programática antes de require_live().
constraints:
  - Threshold de confiança = 0.6 (hardcoded)
  - Rejeições logadas como warning via emit_log
  - Retorna dict estruturado com reason, rule, value, threshold
notes:
  - MODO FINANCEIRO: threshold hardcoded — calibração futura via config pode ser necessária
