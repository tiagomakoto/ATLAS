---
uid: B66
title: N_MINIMO grid competitivo — critério bidimensional (volume + dispersão temporal)
status: open
opened_at: 2026-04-30
closed_at:
opened_in: [[BOARD/atas/2026-04-30_tune_v31_estrutural_fixo_n_minimo]]
closed_in:
decided_by:
system: delta_chaos

description: >
  N_MINIMO=20 é critério empírico unidimensional — volume de trades apenas.
  Board identificou que amostra concentrada em evento único (ex. COVID 2020)
  invalida a calibração independente do tamanho. Proposta de Thorp: adicionar
  N_anos_com_trades ≥ 2 como segundo eixo obrigatório.
  Risco adicional (Eifert): com n=20 e 9 combos Optuna, overfitting é possível —
  o threshold pode ser permissivo demais, não restritivo demais.

gatilho:
  - Após 1º trimestre de paper trading com dados reais de frequência por regime

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/tune.py]]

resolution:

notes:
  - Thorp propõe: N_trades ≥ 20 AND N_anos_com_trades ≥ 2
  - Eifert: overfitting com n=20 e 9 graus de liberdade é risco real — considerar elevar N_MINIMO junto com critério temporal
  - Taleb: heterogeneidade temporal importa mais que tamanho — concentração em regime BAIXA de 2020 invalida qualquer n
  - Regimes raros (PANICO, BAIXA) podem ser estruturalmente incapazes de atingir qualquer N_MINIMO em 5 anos
---
