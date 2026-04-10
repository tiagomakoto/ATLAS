---
uid: B30
title: TUNE v2.0 — máscara REFLECT e dimensão de estratégias alternativas
status: open
opened_at: 2026-03-23
closed_at:
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in:
decided_by:
system: delta_chaos

description: >
  TUNE v2.0 pendente Chan: (1) implementar máscara de ciclos REFLECT
  excluindo Edge C e D da simulação; (2) adicionar dimensão de estratégias
  alternativas por regime — CSP vs BULL_PUT_SPREAD em NEUTRO_BULL,
  BEAR_CALL_SPREAD vs outras em NEUTRO_BEAR.

gatilho:
  - após primeiro trimestre de paper trading
  - dependência: [[BOARD/tensoes_abertas/B42_TUNE_v2]]

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]

resolution:

notes:
  - TUNE v2.0 deve rodar com máscara REFLECT — resultado sem máscara é subótimo
---
