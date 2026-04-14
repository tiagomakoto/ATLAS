---
date: 2026-04-13
session_type: off-ata
system: delta_chaos

decisions:
  - Campo 'regime_estrategia' renomeado para 'regime' em toda a codebase
  - orbit.py corrigido como único ponto de produção do campo
  - 2119 ciclos migrados nos JSONs de ativos via migrate_regime.py
  - Expansão futura (múltiplas estratégias por regime) pertence ao dict
    'estrategias' do master JSON — não ao campo 'regime' do historico[]

tensoes_abertas: []

tensoes_fechadas:
  - [[BOARD/decisoes/Q12_regime_estrategia_padronizado_regime]]

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]
  - [[SYSTEMS/delta_chaos/modules/EDGE]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]
  - [[SYSTEMS/delta_chaos/modules/TAPE]]

next_actions:
  - Retomar onboarding PRIO3 e BBDC4 com ORBIT corrigido
---
