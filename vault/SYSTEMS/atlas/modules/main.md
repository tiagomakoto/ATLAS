---
uid: mod-atlas-028
version: 1.0.1
status: validated
owner: Chan | Lilian | Board

function: Ponto de entrada da aplicação FastAPI — configura lifespan, CORS, routers, WebSocket endpoint e sanitização de calibrações órfãs na inicialização.
file: atlas_backend/main.py
role: Entry point — inicializa e configura toda a aplicação ATLAS backend.

input: []

output:
- health_check: dict — {status, system, mode, uptime_seconds, timestamp}
- ws_events: WebSocket — endpoint /ws/events para streaming em tempo real

depends_on:
- [[SYSTEMS/atlas/modules/EVENT_BUS]]
- [[SYSTEMS/atlas/modules/API_ROUTES]]
- [[SYSTEMS/atlas/modules/WEBSOCKET]]
- [[SYSTEMS/atlas/modules/CONFIG_MANAGER]]
- [[SYSTEMS/atlas/modules/runtime_mode]]

depends_on_condition: []

used_by: []

intent:
- Centralizar toda a inicialização do backend em um único módulo. Sanitização de calibrações órfãs previne estados fantasmas após restart.

constraints:
- _sanitize_stale_calibracoes marca steps running como paused na inicialização
- WindowsProactorEventLoopPolicy aplicado em win32
- CORS permissivo (allow_origins=['*']) — aceito para paper trading
- _started_at = datetime.utcnow() — timestamp de início do servidor
- 7 routers registrados: config, modules, mode, ativos, cycle, config_diff, delta_chaos
- lifespan inicia event_dispatcher como task assíncrona

notes:
- 2026-04-22 — módulo criado automaticamente a partir de atlas_backend/main.py
- 2026-04-25 — vault validado: campos BOARD_REVIEW_REQUIRED preenchidos via análise de código
- _started_at usa datetime.utcnow() (deprecated) — divergência com timeutils.iso_utc()