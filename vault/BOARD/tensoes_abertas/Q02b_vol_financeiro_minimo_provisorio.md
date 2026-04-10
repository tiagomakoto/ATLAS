---
uid: Q2b
title: volume_financeiro_minimo=10000 provisório — calibrar após primeiro mês
status: open
opened_at: 2026-03-23
closed_at:
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in:
decided_by:
system: delta_chaos

description: >
  O valor volume_financeiro_minimo=10000 em delta_chaos_config.json é
  provisório. Calibrar após primeiro mês de paper trading verificando
  quantas candidatas são eliminadas por EOD.

gatilho:
  - após primeiro mês de paper trading

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/FIRE]]

resolution:

notes:
  - Se > 30% eliminadas por EOD, reduzir. Se < 5%, aumentar.
  - Relacionado a B39
---
