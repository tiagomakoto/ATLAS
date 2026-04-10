---
uid: B31
title: Calmar ratio como métrica primária — alavancas mapeadas
status: open
opened_at: 2026-03-23
closed_at:
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in:
decided_by:
system: delta_chaos

description: >
  Calmar ratio atual: 3.57 (portfólio 3 ativos). Quatro alavancas
  identificadas para melhora: (1) mais ativos descorrelacionados —
  BBAS3 prioritário após primeiro trimestre; (2) mais capital;
  (3) dois vencimentos simultâneos em Edge A; (4) otimização TP/STOP
  com REFLECT integrado — último por risco de overfitting.

gatilho:
  - alavanca 1: após primeiro trimestre, BBAS3 disponível
  - alavanca 3: avaliar após paper trading
  - alavanca 4: após TUNE v2.0 com máscara REFLECT

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]

resolution:

notes:
  - Calmar ratio subiu 38% de 2.59 (2 ativos) para 3.57 (3 ativos)
---
