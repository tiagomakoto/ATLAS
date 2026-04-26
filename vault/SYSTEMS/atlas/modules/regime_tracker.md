---
uid: mod-atlas-044
version: 1.0
status: validated
owner: Chan
function: Rastreia regime ORBIT corrente e detecta transições — emite evento regime_update a cada atualização e alert warning em mudança de regime.
file: atlas_backend/core/regime_tracker.py
role: Tracker de regime — detecta e notifica transições de regime de mercado em tempo real.
input:
  - new_regime: str — regime atual do ORBIT
  - confidence: float — confiança da classificação
output:
  - update_regime: None — emite regime_update event e alert (se transição)
depends_on:
  - [[SYSTEMS/atlas/modules/EVENT_BUS]]
depends_on_condition: []
used_by: []
intent:
  - Superficiar transições de regime ao frontend em tempo real — mudanças de regime são eventos críticos para decisão operacional.
constraints:
  - current_regime = None (inicial)
  - Emite regime_update a cada chamada
  - Emite alert level=warning quando regime muda
  - Detecção de transição por comparação com current_regime anterior
notes:
  - Complementar ao ORBIT — regime_tracker é a camada ATLAS de notificação em tempo real
