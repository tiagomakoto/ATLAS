---
uid: mod-delta-010
version: 1.0
status: draft
owner: Chan | Lilian | Board

function: [BOARD_REVIEW_REQUIRED]
file: atlas_backend/api/routes/delta_chaos.py
role: [BOARD_REVIEW_REQUIRED]

input:
  - <name>: <type + meaning>

output:
  - <name>: <type + meaning>

depends_on:
  - [[SYSTEMS/<system>/modules/...]]

depends_on_condition:
  - <condição>: [[SYSTEMS/<system>/modules/...]]

used_by:
  - [[SYSTEMS/<system>/modules/...]]

intent: [BOARD_REVIEW_REQUIRED]
  - [BOARD_REVIEW_REQUIRED] ou descrição explícita

constraints: [BOARD_REVIEW_REQUIRED]
  - <regras / invariantes / thresholds literais>

notes:
  - 2026-04-13 — módulo criado automaticamente a partir de atlas_backend/api/routes/delta_chaos.py
  - <edge cases ou riscos>