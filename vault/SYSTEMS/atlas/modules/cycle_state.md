---
uid: mod-atlas-040
version: 1.0
status: validated
owner: Chan
function: Mantém snapshot mutável do ciclo de trading corrente (ativo, regime, confiança, posição, P&L) e emite evento cycle_update a cada mudança.
file: atlas_backend/core/cycle_state.py
role: Estado do ciclo — fonte de verdade para o snapshot atual do ciclo de trading.
input:
  - data: dict — campos a mesclar no cycle_state
output:
  - update_cycle: dict — evento cycle_update emitido com estado mesclado
depends_on:
  - [[SYSTEMS/atlas/modules/EVENT_BUS]]
depends_on_condition: []
used_by:
  - [[SYSTEMS/atlas/modules/ATLAS_DC_RUNNER]]
intent:
  - Prover estado consistente do ciclo corrente para todo o backend e frontend em tempo real.
constraints:
  - cycle_state = {ativo: None, regime: None, regime_confianca: None, posicao: False, pnl: 0.0}
  - Merge parcial — data é mesclado, não substituído
  - Evento cycle_update emitido a cada update_cycle
notes:
  - Estado global mutável — não thread-safe por si só, depende do event loop assíncrono
