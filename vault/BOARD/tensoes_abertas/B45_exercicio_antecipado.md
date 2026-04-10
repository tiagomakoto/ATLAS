---
uid: B45
title: Exercício antecipado não modelado
status: open
opened_at: 2026-03-23
closed_at:
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in:
decided_by:
system: delta_chaos

description: >
  O sistema não modela risco de exercício antecipado em opções americanas.
  Para o mercado brasileiro (B3), opções sobre ações são americanas.
  Impacto não quantificado.

gatilho:
  - [BOARD_REVIEW_REQUIRED] — definir prioridade e abordagem de modelagem

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/BOOK]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]

resolution:

notes:
  - BOVA11 opera com opções sobre ETF — verificar se americanas ou europeias
---
