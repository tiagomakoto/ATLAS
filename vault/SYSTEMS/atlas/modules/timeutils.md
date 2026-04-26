---
uid: mod-atlas-029
version: 1.0.1
status: validated
owner: Chan | Lilian | Board

function: Fornece timestamp UTC canônico em formato ISO 8601 com offset explícito (+00:00) para serialização JSON e emissão WebSocket.
file: atlas_backend/core/timeutils.py
role: Utilitário de timestamp — garante que toda serialização temporal no sistema carregue offset UTC explícito.

input: []

output:
- iso_utc: str — timestamp ISO 8601 com offset +00:00

depends_on: []

depends_on_condition: []

used_by:
- [[SYSTEMS/atlas/modules/EVENT_BUS]]
- [[SYSTEMS/atlas/modules/ATLAS_DC_RUNNER]]
- [[SYSTEMS/atlas/modules/DATA_READERS]]

intent:
- Eliminar ambiguidade entre timestamps locais e UTC no pipeline de eventos. Frontend new Date(isoStr) interpreta corretamente apenas com offset explícito.

constraints:
- iso_utc() retorna string com sufixo +00:00 — nunca timestamp naive
- Usa datetime.now(timezone.utc) — não datetime.utcnow() (deprecated)

notes:
- 2026-04-23 — módulo criado automaticamente a partir de atlas_backend/core/timeutils.py
- 2026-04-25 — vault validado: campos BOARD_REVIEW_REQUIRED preenchidos via análise de código