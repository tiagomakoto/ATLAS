---
uid: Q11
title: TUNE v1.1 VALE3 potencialmente afetado por Q10
status: closed
opened_at: 2026-03-23
closed_at: 2026-04-12
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in: [[BOARD/atas/2026-04-12_Q10_regime_estrategia]]
decided_by: CEO
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
  - Hipótese não materializada. O TUNE lê o campo regime do histórico
    (raw.get("regime")), não regime_estrategia. O campo regime estava
    correto em todos os 518 ciclos históricos durante toda a vigência
    de Q10 — os sub-regimes (NEUTRO_BULL, NEUTRO_BEAR etc.) estavam
    gravados e íntegros. TUNE de VALE3 operou sem contaminação.

notes:
  - dependência explícita: [[BOARD/decisoes/Q10_S6_VALE3_congelado]]
  - encerrada na mesma sessão de Q10 — diagnóstico derivado direto
---
