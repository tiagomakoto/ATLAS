---
uid: B38
title: BOVA11 NEUTRO_TRANSICAO sem estratégia
status: open
opened_at: 2026-03-23
closed_at:
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in:
decided_by:
system: delta_chaos

description: >
  Regime NEUTRO_TRANSICAO para BOVA11 não possui estratégia mapeada no FIRE.
  VALE3 também bloqueada no mesmo regime com sizing=0. Sem definição de
  estratégia, o sistema não opera neste regime.

gatilho:
  - definição explícita de estratégia para NEUTRO_TRANSICAO

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]

resolution:

notes:
  - BOVA11 NEUTRO_BULL também bloqueado por edge ausente — tensão relacionada
  - VALE3 bloqueada: sizing=0 no mesmo regime
---
