---
uid: B38
title: BOVA11 NEUTRO_TRANSICAO sem estratégia
status: closed
opened_at: 2026-03-23
closed_at: 2026-04-30
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in: [[BOARD/atas/2026-04-30_b63_fechamento_regimes_lateral]]
decided_by: CEO
system: delta_chaos

description: >
  Regime NEUTRO_TRANSICAO para BOVA11 não possuía estratégia mapeada no FIRE.
  VALE3 também bloqueada no mesmo regime com sizing=0. Sem definição de
  estratégia, o sistema não operava neste regime.

gatilho:
  - definição explícita de estratégia para NEUTRO_TRANSICAO

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]

resolution:
  - Obsoleta por B63 (2026-04-30). NEUTRO_TRANSICAO eliminado do universo
    de regimes — confirmado como artefato de fronteira do ORBIT (~7% frequência
    constante), não regime de mercado. Redistribuído para LATERAL via
    _redistribuir_transicao em orbit.py. Não há estratégia a definir.

notes:
  - Fechada por obsolescência — não requer ação de implementação.
  - B63 é a decisão de referência.
---
