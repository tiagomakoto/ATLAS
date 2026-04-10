---
uid: B26
title: Divergência GATE vs TUNE — TP/STOP em VALE3
status: open
opened_at: 2026-03-22
closed_at:
opened_in: [[BOARD/atas/2026-03-22_reflect_arquitetura]]
closed_in:
decided_by:
system: delta_chaos

description: >
  GATE sugere TP=0.75 STOP=1.0x (IR=+5.019) para VALE3.
  TUNE v1.1 aprovou TP=0.90 STOP=2.0 (IR=+4.211).
  TUNE vence metodologicamente — mas divergência precisa ser monitorada
  em paper trading para confirmar robustez do TUNE.

gatilho:
  - monitorar durante paper trading — reavaliar com TUNE v2.0

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]

resolution:

notes:
  - Parâmetros ativos: TP=0.90 STOP=2.0 (decisão TUNE)
---
