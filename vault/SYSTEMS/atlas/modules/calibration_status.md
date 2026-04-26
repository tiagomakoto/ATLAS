---
uid: mod-atlas-039
version: 1.0
status: validated
owner: Chan
function: Rastreia tempo decorrido desde a última calibração TUNE e emite evento de staleness via WebSocket.
file: atlas_backend/core/calibration_status.py
role: Monitor de staleness — permite ao frontend alertar quando dados de calibração estão desatualizados.
input: []
output:
  - emit_staleness: dict — evento calibration_staleness com seconds_elapsed
  - update_calibration: None — atualiza last_calibration para UTC now
depends_on:
  - [[SYSTEMS/atlas/modules/EVENT_BUS]]
depends_on_condition: []
used_by: []
intent:
  - Superficiar ao CEO quando a calibração TUNE está stale — dados desatualizados podem levar a decisões operacionais ruins.
constraints:
  - last_calibration inicializado com datetime.utcnow() na importação
  - emit_staleness computa (utcnow - last_calibration).total_seconds()
notes:
  - Staleness é métrica informativa — não bloqueia operação automaticamente
