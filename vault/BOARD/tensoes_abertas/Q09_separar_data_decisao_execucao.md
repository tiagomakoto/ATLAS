---
uid: Q9
title: Separar data_decisao de data_execucao no BOOK e FIRE — pré-live
status: open
opened_at: 2026-03-23
closed_at:
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in:
decided_by:
system: delta_chaos

description: >
  Na fase live, data_decisao (EOD, dia anterior) e data_execucao
  (abertura, dia seguinte) devem ser campos separados no BOOK e FIRE.
  Não bloqueia paper trading — implementar antes da Fase live.

gatilho:
  - antes da migração para capital real

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/BOOK]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]

resolution:

notes:
---
