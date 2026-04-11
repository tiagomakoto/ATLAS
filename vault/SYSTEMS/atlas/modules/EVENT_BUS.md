---
uid: mod-atlas-002
version: 1.0
status: validated
owner: Chan

function: Barramento de eventos assíncrono do backend, encaminhando logs, status do DC e métricas de health para disparo unificado pelo WebSocket.
file: atlas_backend/core/event_bus.py, atlas_backend/core/event_logger.py
role: Barramento de eventos — canal centralizado para push de dados assíncronos ao frontend.

input:
  - event_type: str — tipo do evento logado/emitido
  - modulo: str — o módulo de origem (ex: "TAPE", "ORBIT")
  - status: str — status emitido

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

notes:
  - `health_monitor` roda autonomamente `await asyncio.sleep(10)` publicando via WebSocket sem invocar request explícito.
---
