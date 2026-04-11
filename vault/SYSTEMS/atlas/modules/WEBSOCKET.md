---
uid: mod-atlas-005
version: 1.0
status: validated
owner: Chan

function: Controlador persistente para stream via WebSocket (FastAPI). Mantém conexões com UI.
file: atlas_backend/api/websocket/stream.py
role: Tunel bidirecional de comunicação real-time

input:
  - WebSocketConnections — cliente web que conecta.
  - events — dados inseridos/chamados por `manager.broadcast()`.

output:
  - Streams strings serializadas via ws (JSON frame payloads).

depends_on:
  - [[SYSTEMS/atlas/modules/EVENT_BUS]]

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/UI_CORE]]

intent:
  - Prover meio instantâneo, unificado por onde rodam alertas de processos em tempo real, monitoramento global de saude via events queue, minimizando pools REST do frontend.

constraints:
  - N/A
  
notes:
  - `manager` global faz broadcast incondicional em todas conexões abertas listadas internamente.
---
