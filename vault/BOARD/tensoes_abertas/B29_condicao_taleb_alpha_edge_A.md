---
uid: B29
title: Condição Taleb — alpha Edge A ativo só após primeiro trimestre
status: open
opened_at: 2026-03-23
closed_at:
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in:
decided_by:
system: delta_chaos

description: >
  Condição imposta por Taleb: alpha do Edge A permanece inativo
  (Edge A = Edge B = mult 1.0) até o primeiro trimestre de paper
  trading com divergência real calculada. Não implementada em código
  como flag temporal.

gatilho:
  - após primeiro trimestre de paper trading com divergência ativa

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]
  - [[SYSTEMS/delta_chaos/modules/TAPE]]

resolution:

notes:
  - Relacionado a B1 (cap máximo do alpha)
  - Relacionado a B11 (calibração pesos via Optuna)
---
