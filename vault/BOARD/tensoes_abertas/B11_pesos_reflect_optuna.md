---
uid: B11
title: Pesos REFLECT 0.33/0.33/0.33 — calibração via Optuna pendente
status: open
opened_at: 2026-03-22
closed_at:
opened_in: [[BOARD/atas/2026-03-22_reflect_arquitetura]]
closed_in:
decided_by:
system: delta_chaos

description: >
  Os pesos dos três componentes do REFLECT são prior de máxima ignorância
  (0.33 cada). Calibração via Optuna aguarda primeiro trimestre de paper
  com os três componentes ativos simultaneamente.

gatilho:
  - mínimo 24 ciclos com três componentes ativos
  - melhoria mínima 20% no Calmar ratio como condição para mudar pesos

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]
  - [[SYSTEMS/delta_chaos/modules/TAPE]]

resolution:

notes:
  - Proteção contra overfitting: mudança de pesos só com evidência forte
  - Pesos em delta_chaos_config.json → reflect.weights
---
