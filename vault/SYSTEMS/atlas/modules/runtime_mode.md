---
uid: mod-atlas-042
version: 1.0
status: validated
owner: Chan
function: Chave global de segurança entre observe (paper/análise) e live (trading real) — require_live() é o hard gate antes de qualquer execução de ordem.
file: atlas_backend/core/runtime_mode.py
role: Guarda de modo — bloqueia execução de ordens reais quando em modo observe.
input:
  - mode: str — 'observe' ou 'live'
output:
  - is_observe: bool — True se modo observe
  - require_live: None ou RuntimeError('EXECUTION_BLOCKED_OBSERVE_MODE')
  - get_mode: str — modo atual
  - set_mode: str — novo modo
depends_on: []
depends_on_condition: []
used_by:
  - [[SYSTEMS/atlas/modules/execution_engine]]
  - [[SYSTEMS/atlas/modules/API_ROUTES]]
intent:
  - Prevenir execução acidental de ordens reais. require_live() é o hard gate chamado antes de qualquer ordem.
constraints:
  - MODE default = 'observe'
  - Valores válidos: 'observe', 'live'
  - set_mode levanta ValueError para modo inválido
  - require_live levanta RuntimeError se MODE != 'live'
notes:
  - MODO FINANCEIRO: este módulo é crítico para segurança — nunca modificar sem revisão do CEO
