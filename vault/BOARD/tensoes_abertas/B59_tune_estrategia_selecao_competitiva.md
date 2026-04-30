---
uid: B59
title: TUNE v3.0 → v3.1 — implementação completa + SCAN aprovado
status: closed
opened_at: 2026-04-25
closed_at: 2026-04-29
opened_in: [[BOARD/atas/2026-04-25_tune_v3_eleicao_competitiva]]
closed_in: [[BOARD/atas/2026-04-29_tune_v31_implementacao_scan]]
decided_by: Board + CEO + SCAN
system: delta_chaos

description: >
  TUNE v3.0 evoluiu para v3.1 em sessão de 2026-04-29. A arquitetura
  original de eleição competitiva via Optuna foi reformulada em duas
  etapas sequenciais (A→B→C) após auditoria de Chan identificar 5
  problemas estruturais (P1–P5).

  v3.1 implementado e aprovado por SCAN:
  - Etapa A: eleição por grid fixo 3×3 + mediana IR (sem Optuna)
  - Etapa B: calibração TP/Stop via Optuna com estratégia fixada
  - Etapa C: gate de anomalia + aplicação automática
  - sizing_config/regimes_sizing removidos da simulação (B56)
  - Endpoints confirmar-regime e confirmar-todos deprecados com 410
  - confirmar-regime-anomalia implementado com run_id obrigatório

resolution:
  - tune.py reescrito como TUNE v3.1 — aprovado por SCAN
  - PATCH_H1 aplicado: sizing_config removido de _simular_para_candidato
  - A1/A2 confirmados resolvidos no router delta_chaos.py
  - SPEC_FRONTEND_TUNE_v31 emitida por Lilian

notes:
  - B61 permanece aberta: migração FIRE/GATE/BOOK para ler tp_por_regime
  - B62 aberta: range Stop do grid revisitar após 1 trimestre paper
  - B64 aberta: origem bug duplicação orbit.py investigar
---
