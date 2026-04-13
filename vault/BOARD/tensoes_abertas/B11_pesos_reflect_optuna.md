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
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/TAPE]]

resolution:

notes:
  - Proteção contra overfitting: mudança de pesos só com evidência forte
  - Pesos em delta_chaos_config.json → reflect.weights
  - Decisão conjunta sessão 2026-04-12: Optuna adotado como stack compartilhado
    para TUNE v2.0 e REFLECT v2.0 — mesmo framework, mesma biblioteca,
    mesma filosofia de busca nos dois módulos. SOTA em otimização bayesiana
    aplicado consistentemente. Implementar Optuna isolado em um módulo sem
    o outro é inconsistência metodológica — decisão é conjunta ou não é.
  - Simons: espaço de busca TUNE inclui TP/STOP, janela de teste e estratégia
    por regime como hiperparâmetros — TPE sampler adequado para espaços mistos
  - Eifert: objetivo Calmar do REFLECT pode ser métrica secundária no Optuna
    do TUNE — consistência de métrica entre módulos
  - Hamilton: Optuna requer dependência externa nova — requirements.txt,
    seed fixo para reprodutibilidade, teste de compatibilidade no ambiente
  - Conecta com [[BOARD/tensoes_abertas/B42_TUNE_v2]] e [[BOARD/tensoes_abertas/B47_janela_teste_tune]]
---
