---
uid: mod-advantage-008
version: 1.0
status: draft
owner: Chan | Lilian | Board

function: [BOARD_REVIEW_REQUIRED]
file: advantage/src/data_layer/db/schema.py
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

intent: [BOARD_REVIEW_REQUIRED] ou descrição explícita

constraints: [BOARD_REVIEW_REQUIRED] — thresholds literais / invariantes / thresholds literais>

notes:
  - 2026-04-09 — módulo criado automaticamente a partir de advantage/src/data_layer/db/schema.py cases ou riscos>