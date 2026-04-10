---
uid: B36
title: PETR4 adverso em 2025 em qualquer configuração TUNE v1.1
status: open
opened_at: 2026-03-23
closed_at:
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in:
decided_by:
system: delta_chaos

description: >
  PETR4 teve P&L negativo em 2025 em todas as configurações testadas
  no TUNE v1.1. REFLECT detectou Edge D em ago/set 2025. Deterioração
  pode ser estrutural ou cíclica — não determinado.

gatilho:
  - monitorar em paper trading
  - recalibrar com TUNE v2.0 antes de escalar capital

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]

resolution:

notes:
  - Baseline -R$235, TP=0.90 -R$331 em 2025
  - REFLECT funcionando passivamente — Edge D detectado corretamente
---
