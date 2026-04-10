---
uid: B1
title: Cap máximo do alpha em Edge A não definido
status: open
opened_at: 2026-03-22
closed_at:
opened_in: [[BOARD/atas/2026-03-22_reflect_arquitetura]]
closed_in:
decided_by:
system: delta_chaos

description: >
  O parâmetro max_cap_alpha do Edge A não foi calibrado empiricamente.
  Valor atual é placeholder conservador. Calibração depende do TUNE de
  sizing da Fase 2.

gatilho:
  - TUNE de sizing Fase 2

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]
  - [[SYSTEMS/delta_chaos/modules/TAPE]]

resolution:

notes:
  - alpha = clip((reflect_score - threshold_A) × alpha_factor, 0, max_cap_alpha)
  - Condição Taleb (B29): alpha ativo somente após primeiro trimestre de paper
---
