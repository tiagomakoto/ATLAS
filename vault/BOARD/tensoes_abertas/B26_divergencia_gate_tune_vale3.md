---
uid: B26
title: Divergência GATE vs TUNE — TP/STOP em VALE3
status: closed
opened_at: 2026-03-22
closed_at: 2026-04-25
opened_in: [[BOARD/atas/2026-03-22_reflect_arquitetura]]
closed_in: [[BOARD/atas/2026-04-25_hardreset_ativos]]
decided_by: CEO
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

resolution: >
  Fechada por obsolescência em 2026-04-25. O hardreset completo dos ativos
  descartou todos os parâmetros do TUNE v1.1. O TUNE v3.0 produziu
  TP=0.65/STOP=1.50 para VALE3 — convergência para parâmetros mais
  conservadores, distantes de ambos os valores originais da tensão.
  O único paper trade executado (B0001 BOVA11) foi sob TUNE v1.0,
  portanto o gatilho "monitorar em paper trading" nunca foi atingido.
  A divergência relevante atual em VALE3 é E5 ORBIT (IR temporal),
  não a divergência GATE vs TUNE de TP/STOP — questão distinta,
  sem B-code aberto.

notes:
  - Parâmetros ativos: TP=0.90 STOP=2.0 (decisão TUNE v1.1) — descartados no hardreset
---
