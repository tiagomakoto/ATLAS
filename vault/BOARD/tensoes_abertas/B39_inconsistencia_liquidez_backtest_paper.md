---
uid: B39
title: Inconsistência backtest vs paper no filtro de liquidez
status: open
opened_at: 2026-03-23
closed_at:
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in:
decided_by:
system: delta_chaos

description: >
  Backtest usava volume > 0. Paper usou VOL_FIN_MIN=10000 brevemente.
  Decisão atual: volume > 0 em ambos. Calibrar empiricamente após
  primeiro trimestre verificando quantas candidatas são eliminadas por EOD.

gatilho:
  - após primeiro trimestre de paper trading

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/delta_chaos/modules/TAPE]]

resolution:

notes:
  - Se > 30% eliminadas, reduzir threshold. Se < 5%, aumentar.
---
