---
uid: B56
title: REFLECT — sizing por estado A/B/C/D/T e eliminação de regimes_sizing do JSON
status: closed
opened_at: 2026-04-24
closed_at: 2026-04-29
opened_in: [[BOARD/atas/2026-04-24_reflect_estados_sizing]]
closed_in: [[BOARD/atas/2026-04-29_fechamento_b53_b54_b55_b56_b57]]
decided_by: Board + CEO
system: delta_chaos

description: >
  Duas decisões de design aprovadas em 2026-04-24:
  1. SIZING POR ESTADO REFLECT (canônico): lookup A=1.0, B=1.0, C=0.5, D=0.0, T=0.0.
  2. REGIMES_SIZING NO JSON FORMALMENTE REDUNDANTE — REMOVER.

gatilho:
  - implementação: reflect_sizing_calcular() usa lookup por estado
  - remoção de regimes_sizing dos JSONs e do código tape.py
  - calibração de C via B30 quando disponível

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]
  - [[SYSTEMS/delta_chaos/modules/EDGE]]
  - [[SYSTEMS/delta_chaos/modules/TAPE]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]

resolution: >
  Implementado. reflect_sizing_calcular() em edge.py usa lookup por estado
  (A=1.0, B=1.0, C=0.5, D=0.0, T=0.0, E=0.0 legado). sizing_orbit × reflect_mult
  aplicado em _executar_backtest e _executar_paper. TODO alpha A (B01/B29)
  adicionado na linha "A": 1.0. TODO revisão C=0.5 (PE-007, condição: 50 ciclos C
  + B30) adicionado na linha "C": 0.5. regimes_sizing e REGIMES_SIZING_PADRAO
  removidos de tape.py em 3 etapas — zero referências confirmadas por coder.
  JSONs existentes com o campo são inertes (ignorados na próxima leitura).
  Suite 76/76 verde. SCAN aprovado 2026-04-29.

notes:
  - PE-007: C=0.5 provisório. Condição de revisão: B30 implementado + 50 ciclos C observados
  - Alpha de A aguarda B01/B29 — documentado como TODO no código
  - JSONs históricos com regimes_sizing: campo ignorado na leitura, não requer migração ativa
  - AUDITORIA SCAN 2026-04-29: APROVADO ✅
---
