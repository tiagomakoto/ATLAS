---
uid: mod-atlas-014
version: 1.0.1
status: draft
owner: Chan | Lilian | Board

function: [BOARD_REVIEW_REQUIRED]
file: atlas_ui/src/store/systemStore.js
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
  - 2026-04-13: código modificado — systemStore.js
  - 2026-04-12 — módulo criado automaticamente a partir de atlas_ui/src/store/systemStore.js
  - <edge cases ou riscos>