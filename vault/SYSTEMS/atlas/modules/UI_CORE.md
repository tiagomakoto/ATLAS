---
uid: mod-atlas-009
version: 1.0
status: draft
owner: Chan

function: Orquestração de componentes front-end, estado web e renderização da UI (React.js).
file: atlas_ui/src/App.jsx, atlas_ui/src/hooks/useWebSocket.js, atlas_ui/src/store/systemStore.js, atlas_ui/src/components/*, atlas_ui/src/layouts/*
role: Exibição visual (SPA) — único ponto de interação humana (leitura e botão) no ecossistema ATLAS.

input:
  - cliques e views do usuário
  - WS Events 
  - Rest API Queries

output:
  - DOM Render

depends_on:
  - [[SYSTEMS/atlas/modules/API_ROUTES]]
  - [[SYSTEMS/atlas/modules/WEBSOCKET]]

depends_on_condition:

used_by:
  - Board

intent:
  - Ser uma "Dashboard Cega" de controle. O front não calcula, não reflete inteligência e não lida com arquivos cruamente. Ele mapeia state.
  
constraints:
  - Tudo orbita chamadas de hook (`useWebSocket`, `Fetch`). Nenhum componente persiste arquivos na interface isolada.

notes:
  - Stores (Zustand provável) armazenam em memory buffers baseados em events injetados via ws (`store/systemStore.js`).
---
