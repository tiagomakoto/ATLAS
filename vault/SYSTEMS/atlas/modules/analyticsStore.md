---
uid: mod-atlas-047
version: 1.0
status: validated
owner: Chan
function: Store Zustand para dados de analytics (distribuição, ACF, fat tails, walk-forward) com tolerância a camelCase e snake_case e staleness tracking.
file: atlas_ui/src/store/analyticsStore.js
role: Estado de analytics — fonte de verdade frontend para métricas estatísticas e frescor de dados.
input:
  - data: dict — dados de analytics do backend (distribution, acf, fatTails/fat_tails, walkForward/walk_forward)
  - event: dict — evento WebSocket cycle_update
output:
  - useAnalyticsStore: Zustand hook — {distribution, acf, fatTails, walkForward, staleness, setAnalytics, clear, update}
depends_on: []
depends_on_condition: []
used_by:
  - [[SYSTEMS/atlas/modules/UI_CORE]]
intent:
  - Centralizar estado de analytics no frontend com tolerância a variações de nomenclatura do backend.
constraints:
  - setAnalytics aceita fatTails e fat_tails, walkForward e walk_forward
  - staleness = Date.now() — timestamp Unix em milissegundos
  - update reage apenas a cycle_update events
  - clear reseta tudo para null/0
notes:
  - Dual camelCase/snake_case é compatibilidade retroativa — normalizar no backend é preferível a longo prazo
