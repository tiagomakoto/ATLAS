---
uid: mod-atlas-036
version: 1.0
status: validated
owner: Chan
function: Guarda de instância única via file lock PID — impede múltiplos processos ATLAS simultâneos com auto-cleanup.
file: atlas_backend/core/access_control.py
role: Lock de processo — garante que apenas uma instância ATLAS executa por vez.
input: []
output:
  - acquire_lock: None — cria /tmp/atlas.lock com PID ou levanta RuntimeError('ATLAS_ALREADY_RUNNING')
  - release_lock: None — remove lock file
depends_on: []
depends_on_condition: []
used_by: []
intent:
  - Prevenir concorrência de processos ATLAS que poderia corromper dados ou criar ordens duplicadas.
constraints:
  - LOCK_FILE = /tmp/atlas.lock
  - acquire_lock levanta RuntimeError se lock já existe
  - release_lock registrado via atexit e SIGTERM handler
  - Auto-cleanup em saída normal e SIGTERM
notes:
  - Lock file em /tmp — não sobrevive a reboot do sistema
  - Stale locks (processo morto sem cleanup) requerem remoção manual
