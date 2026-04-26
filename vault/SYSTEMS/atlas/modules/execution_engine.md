---
uid: mod-atlas-045
version: 1.0
status: validated
owner: Chan
function: Pipeline de execução de ordens — gatekeeper (confidence >= 0.6) → runtime_mode (must be live) → execução placeholder. Toda exceção capturada e roteada via emit_error.
file: atlas_backend/core/execution_engine.py
role: Executor de ordens — ponto único de entrada para envio de ordens ao mercado B3.
input:
  - signal: dict — sinal de trade com campo confidence
output:
  - execute_order: None — executa ordem ou loga bloqueio/rejeição
depends_on:
  - [[SYSTEMS/atlas/modules/gatekeeper]]
  - [[SYSTEMS/atlas/modules/runtime_mode]]
  - [[SYSTEMS/atlas/modules/terminal_stream]]
depends_on_condition: []
used_by: []
intent:
  - Centralizar toda execução de ordens em um único ponto com verificação de confiança e modo. Nenhuma ordem deve bypassar este pipeline.
constraints:
  - Sequência obrigatória: gate_decision → require_live → execução
  - gatekeeper rejeita confidence < 0.6
  - require_live bloqueia em modo observe
  - Execução real é placeholder — não conectada à B3 ainda
  - Toda exceção capturada e emitida via emit_error
notes:
  - MODO FINANCEIRO: este módulo é crítico para segurança — nunca modificar sem revisão do CEO
  - Placeholder de execução — integração com corretora é Fase 2
