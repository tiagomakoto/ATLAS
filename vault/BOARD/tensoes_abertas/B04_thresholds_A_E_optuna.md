---
uid: B4
title: Thresholds A–E aguardam calibração via Optuna
status: open
opened_at: 2026-03-22
closed_at:
opened_in: [[BOARD/atas/2026-03-22_reflect_arquitetura]]
closed_in:
decided_by:
system: delta_chaos

description: >
  Os thresholds que definem transições entre Edge A–E são placeholders
  conservadores. Calibração via Optuna maximizando Calmar ratio depende
  de coleta mínima de 15 ciclos EOD com divergência ativa.

gatilho:
  - 15 ciclos EOD com divergência ativa coletados
  - distribuição empírica do score diagnosticada

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]
  - [[SYSTEMS/delta_chaos/modules/TAPE]]

resolution:

notes:
  - Célula de calibração a ser implementada por Chan
  - Roda sobre reflect_all_cycles_history
  - Placeholders atuais conservadores o suficiente para operar durante coleta
---
