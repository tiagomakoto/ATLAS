---
uid: mod-atlas-004
version: 1.0.4
status: validated
owner: Chan

function: Fornece e recebe requisições via endpoints HTTP RESTful para gerenciar modos, ler arquivos, ativar módulos, listar ativos e fornecer logs.
file: atlas_backend/api/routes/ativos.py, atlas_backend/api/routes/config.py, atlas_backend/api/routes/cycle.py, atlas_backend/api/routes/delta_chaos.py, atlas_backend/api/routes/mode.py, atlas_backend/api/routes/modules.py, atlas_backend/api/routes/report.py, atlas_backend/main.py
role: Interface Externa (API)

input:
  - Requests HTTP (GET, POST, PUT) com payloads JSON validados via FastAPI.

output:
  - Respostas JSON estruturadas.

depends_on:
  - [[SYSTEMS/atlas/modules/ATLAS_DC_RUNNER]]
  - [[SYSTEMS/atlas/modules/DATA_READERS]]
  - [[SYSTEMS/atlas/modules/CONFIG_MANAGER]]

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/UI_CORE]]

intent:
  - Expor as capacidades do ATLAS e leitura estado offline gerado via Delta Chaos para os hooks de frontend em uma API fracamente acoplada (stateless).

constraints:
  - FastAPI utiliza o policy `WindowsProactorEventLoopPolicy` no init do Windows.
  - Endpoints importam a lógica de runtime delegando a pesada IO / Threading por baixo de abstrações async.

notes:
  - 2026-04-26: código modificado — ativos.py
  - 2026-04-26: código modificado — ativos.py
  - 2026-04-17: código modificado — ativos.py
  - 2026-04-13: código modificado — ativos.py
  - main.py orquestra importações base, adiciona CORS global `allow_origins=["*"]`, e dispara tasks no asgi lifespan context_manager.
---
