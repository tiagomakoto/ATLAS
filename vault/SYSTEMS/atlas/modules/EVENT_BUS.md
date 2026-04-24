---
uid: mod-atlas-002
version: 1.0.2
status: validated
owner: Chan

function: Barramento de eventos assíncrono do backend, encaminhando logs, status do DC e métricas de health para disparo unificado pelo WebSocket. Provê emit_dc_event como API principal para eventos estruturados do Delta Chaos.
file: atlas_backend/core/event_bus.py, atlas_backend/core/event_logger.py
role: Barramento de eventos — canal centralizado para push de dados assíncronos ao frontend.

input:
  - event_type: str — tipo do evento logado/emitido (dc_module_start, dc_module_complete, etc.)
  - modulo: str — o módulo de origem (ex: "TAPE", "ORBIT")
  - status: str — status emitido ("running", "ok", "error")

output:
  - event: dict — evento envelopado na fila (Queue) para o websocket stream
  - health_status: str — status agregado da infraestrutura emitido em "health_update"

depends_on:

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/ATLAS_DC_RUNNER]]
  - [[SYSTEMS/atlas/modules/HEALTH_MONITOR]]
  - [[SYSTEMS/atlas/modules/WEBSOCKET]]

intent:
  - Centralizar a emissão de métricas, status e logs do backend e subprocessos, permitindo que o WebSocket rode um loop limpo `event_dispatcher` escutando a fila global, evitando perdas de thread/socket blocks.

constraints:
  - O dispatcher e o monitor de health rodam em loop contínuo como backgrounds tasks criadas no asgi lifespan (`main.py`).
  - O `event_dispatcher` consome uma `asyncio.Queue` de maneira não-bloqueante.
  - `book_paper.json` possui verificação de threshold "age_hours > 24" para alertar desatualização na task de health_monitor.
  - Módulos obrigatoriamente têm nomes no SET `{"TAPE", "ORBIT", "FIRE", "GATE", "REFLECT"}`.
  - set_main_loop(loop) chamado no lifespan para guardar referência ao loop principal do uvicorn.
  - emit_dc_event é a API principal — gera message amigável, injeta timestamp UTC, e chama emit_event.
  - emit_event usa call_soon_threadsafe para thread-safety entre subprocess threads e o loop principal.
  - health_monitor roda como asyncio.create_task dentro de event_dispatcher — verifica BOOK staleness e ativos parametrizados a cada 10s.
  - DC_EVENT_TYPES define 5 tipos: dc_module_start, dc_module_complete, dc_module_progress, dc_module_error, dc_workflow_complete.

notes:
  - 2026-04-23: código modificado — event_bus.py
  - `health_monitor` roda autonomamente `await asyncio.sleep(10)` publicando via WebSocket sem invocar request explícito.
  - emit_dc_event aceita **metadata kwargs arbitrários (ticker, anos, trial, total, ir, etc.)
---
