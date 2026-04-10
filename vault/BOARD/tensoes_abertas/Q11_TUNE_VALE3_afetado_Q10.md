---
uid: Q11
title: TUNE v1.1 VALE3 potencialmente afetado por Q10
status: open
opened_at: 2026-03-23
closed_at:
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in:
decided_by:
system: delta_chaos

description: >
  Se S6 de VALE3 está congelado desde 2024-Q1 (Q10), os parâmetros de
  TUNE v1.1 calibrados para VALE3 podem estar baseados em regime incorreto.
  Hipótese não confirmada — depende de Q10.

gatilho:
  - resolução de Q10

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]

resolution:

notes:
  - não investigar Q11 antes de fechar Q10
  - dependência explícita: [[BOARD/tensoes_abertas/Q10_S6_VALE3_congelado]]
---
