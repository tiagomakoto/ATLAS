---
uid: B42
title: TUNE v2.0 — desenvolvimento pendente
status: closed
opened_at: 2026-03-23
closed_at: 2026-04-13
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in: [[BOARD/atas/2026-04-12_tune_v2_escopo]]
decided_by: CEO
system: delta_chaos

description: >
  TUNE v2.0 não iniciado. Versão atual v1.1 opera em produção.
  Desenvolvimento da v2.0 adiado para pós-primeiro trimestre.

gatilho:
  - pós-primeiro trimestre de operação real

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]

resolution: >
  Implementado em sessão 2026-04-13. Cinco fases entregues e aprovadas por SCAN:

  FASE 1a (B48): campo premio_executado em Leg — fire.py + book.py
    Separar preço simulado (fechamento d0) de preço real de execução (open d1).
    Backward compatible. Aprovado por SCAN.

  FASE 2: Optuna TPE substitui grade fixa de 6 combinações — tune.py
    Espaço: TP [0.40,0.95] step 0.05 | STOP [1.0,3.0] step 0.25 | janela [3,10] anos.
    200 trials | n_startup=50 | early stop patience=50 min_delta=0.001 | seed=42.
    C1/C2/C3 de performance aplicados. Aprovado por SCAN.

  FASE 3: máscara REFLECT exclui ciclos Edge C/D/E — tune.py
    Lê reflect_state por ciclo de reflect_cycle_history[] com fallback permissivo 'B'.
    Aprovado por SCAN.

  FASE 4: tune_diagnostico_estrategia() + tune_aplicar_estrategias() — tune.py
    Diagnóstico de estratégia vencedora por regime via P&L histórico do BOOK.
    Funções isoladas, sem escrita automática. Aprovado por SCAN.

  FASE 5: iv_rank por ciclo — orbit.py v3.6
    Proxy: vol_garch_21d (fallback vol_21d). Percentil sobre histórico do próprio ativo.
    IV_RANK_JANELA como constante de módulo. Aprovado por SCAN.

  FASE 1b: slippage por ativo — aguarda B49 (dados de paper trading).

notes:
  - Q10/Q11 fechadas antes do início (CEO confirmou em sessão)
  - B23 fechada (Optuna 200 trials, steps 0.05/0.25/1)
  - B30 fechada (máscara REFLECT + diagnóstico estratégia implementados)
  - B47 fechada (janela como hiperparâmetro Optuna)
  - B49 aberta — aguarda 1º trimestre paper
  - Dois cosméticos residuais em orbit.py: docstring e __main__ ainda dizem v3.5
---
