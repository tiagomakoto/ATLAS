---
uid: Q10
title: S6 VALE3 congelado desde 2024-Q1
status: open
opened_at: 2026-03-23
closed_at:
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in:
decided_by:
system: delta_chaos

description: >
  O campo S6 (regime_estrategia) de VALE3 está congelado com dados de 2024-Q1.
  Causa desconhecida. Pode indicar falha na atualização do master JSON,
  problema na TAPE ou dado corrompido na fonte.

gatilho:
  - investigação imediata — próxima sessão

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TAPE]]
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]

resolution:

notes:
  - Q11 depende da resolução de Q10
  - VALE3 operacional nos demais campos — apenas S6 afetado
---
