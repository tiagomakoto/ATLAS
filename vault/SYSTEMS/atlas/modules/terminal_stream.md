---
uid: mod-atlas-030
version: 1.0
status: validated
owner: Chan
function: Dual-sink log router — envia cada mensagem simultaneamente para stdout (fallback) e para o event bus WebSocket como evento estruturado.
file: atlas_backend/core/terminal_stream.py
role: Logger dual — garante que toda saída de terminal é visível localmente e transmitida ao frontend em tempo real.
input:
  - msg: str — mensagem de log
  - e: Exception — exceção para emit_error
  - level: str — nível do log (default: info)
output:
  - terminal_log event: dict — {type: terminal_log, message, level}
  - terminal_error event: dict — {type: terminal_error, message, error_type}
depends_on:
  - [[SYSTEMS/atlas/modules/EVENT_BUS]]
depends_on_condition: []
used_by:
  - [[SYSTEMS/atlas/modules/ATLAS_DC_RUNNER]]
  - [[SYSTEMS/atlas/modules/execution_engine]]
  - [[SYSTEMS/atlas/modules/gatekeeper]]
intent:
  - Garantir que logs de subprocessos Delta Chaos chegam ao frontend em tempo real sem perder o fallback stdout.
constraints:
  - emit_log imprime antes de emitir evento — stdout nunca é suprimido
  - emit_error captura tipo e mensagem da exceção
  - Sem nível de log filtering — tudo é transmitido
notes:
  - Usado extensivamente pelo dc_runner para rotear output de subprocessos
