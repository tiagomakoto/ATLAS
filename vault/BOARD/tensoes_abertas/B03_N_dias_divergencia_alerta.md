---
uid: B3
title: N dias de divergência para alerta no REFLECT diário
status: open
opened_at: 2026-03-22
closed_at:
opened_in: [[BOARD/atas/2026-03-22_reflect_arquitetura]]
closed_in:
decided_by:
system: delta_chaos

description: >
  O threshold de dias consecutivos de divergência para emitir alerta
  no REFLECT diário não foi definido. Parâmetro pendente de calibração
  empírica após coleta de dados reais.

gatilho:
  - após primeiro trimestre de paper trading com divergência ativa

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]
  - [[SYSTEMS/delta_chaos/modules/TAPE]]

resolution:

notes:
  - Relacionado a B4 (thresholds A–E via Optuna)
---
