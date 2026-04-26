---
uid: mod-atlas-037
version: 1.0
status: validated
owner: Chan
function: Loop assíncrono infinito que executa backup periódico com intervalo configurável via watchdog limits.
file: atlas_backend/core/backup_scheduler.py
role: Agendador de backup — dispara run_backup em intervalo configurável.
input: []
output:
  - backup_loop: async — executa run_backup a cada backup_interval_seconds
depends_on:
  - [[SYSTEMS/atlas/modules/backup]]
  - [[SYSTEMS/atlas/modules/HEALTH_MONITOR]]
depends_on_condition: []
used_by: []
intent:
  - Automatizar backups periódicos sem intervenção do CEO.
constraints:
  - Intervalo default: 60s (de watchdog.load_limits)
  - RuntimeError capturado e impresso — loop continua
  - Loop infinito — sem condição de parada interna
notes:
  - Falhas de backup não interrompem o loop — apenas log em stdout
