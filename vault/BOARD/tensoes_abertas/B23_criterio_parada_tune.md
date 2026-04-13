---
uid: B23
title: Critério de parada do TUNE — não formalizado em código
status: closed
opened_at: 2026-03-22
closed_at: 2026-04-13
opened_in: [[BOARD/atas/2026-03-22_reflect_arquitetura]]
closed_in: [[BOARD/atas/2026-04-12_tune_v2_escopo]]
decided_by: CEO
system: delta_chaos

description: >
  O TUNE não tem critério de parada formal implementado em código.
  Quando parar de buscar parâmetros, com que amostra mínima, com que
  delta de melhora — não codificado.

gatilho:
  - TUNE v2.0

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]

resolution: >
  Sessão 2026-04-13. CEO confirmou após debate Thorp + Simons + Taleb.

  CONFIGURAÇÃO OPTUNA APROVADA:
  - n_trials: 200
  - Sampler: TPESampler(n_startup_trials=50, seed=42)
  - Early stopping: patience=50 trials sem melhoria, min_delta=0.001 no IR
  - Steps: TP=0.05, STOP=0.25, janela_anos=1 (inteiro)
  - Espaço de busca: TP [0.40, 0.95], STOP [1.0, 3.0], janela [3, 10]
  - Combinações possíveis: 864 (12 × 9 × 8)
  - Cobertura: ~23% com busca inteligente TPE — adequado

  ADVERTÊNCIAS REGISTRADAS:
  - Simons: execução será longa (horas por ativo) — processo batch
  - Taleb: resultado é "melhor para o passado observado"
    Requer PE no vault análogo ao PE-001 após implementação

notes:
  - PE complementar a ser registrado após primeira execução do TUNE v2.0
  - Conecta com B42 (desenvolvimento TUNE v2.0) e B47 (janela como hiperparâmetro)
---
