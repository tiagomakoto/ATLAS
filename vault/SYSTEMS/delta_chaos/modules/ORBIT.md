---
uid: mod-delta-002
version: 3.4.3
status: validated
owner: Chan

function: Classificacao de regime de mercado por ativo. Produz regimes e sub-regimes via walk-forward OLS ridge com cinco camadas de sinais mais S6 para series externas.
file: delta_chaos/orbit.py
role: Classificador de regime — saida alimenta FIRE (estrategia) e EDGE (sizing)

input:
  - master_json: dict — estado do ativo carregado pelo TAPE
  - cfg_ativo: dict — configuracao do ativo (series externas, prior, janelas)

output:
  - regime: str — regime atual (ALTA, NEUTRO_BULL, NEUTRO_BEAR, NEUTRO_LATERAL, NEUTRO_MORTO, NEUTRO_TRANSICAO, BAIXA, RECUPERACAO, PANICO)
  - score_vel: float — velocidade do score de regime (usado pelo REFLECT)
  - regimes_sizing: dict — sizing por regime para o ativo

depends_on:
  - [[SYSTEMS/delta_chaos/modules/TAPE]]

depends_on_condition:

used_by:
  - [[SYSTEMS/delta_chaos/modules/EDGE]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]

intent:
  - Classificar regime com robustez estatistica — walk-forward evita lookahead bias.
  - Vocabulario do ORBIT e exclusivo — nao se mistura com vocabulario do REFLECT.

constraints:
  - Walk-forward OLS ridge — janela 504 dias, recalibracao a cada 126 dias
  - Cinco camadas S1 a S5 mais S6 unificada para series externas
  - Prior padrao 0.20 uniforme — injetado pelo TAPE quando nao existe no master JSON
  - vol_63d adicionado ao master JSON por ciclo
  - Importacao morta de tape_reflect_cycle removida — chamada feita pelo EDGE
  - Vocabulario exclusivo — nao misturar com estados do REFLECT (A-E)

notes:
  - 2026-04-12: código modificado — orbit.py
  - 2026-04-12: código modificado — orbit.py
  - 2026-04-12: código modificado — orbit.py
  - Sub-regimes NEUTRO — NEUTRO_BULL, NEUTRO_BEAR, NEUTRO_LATERAL, NEUTRO_MORTO, NEUTRO_TRANSICAO
  - Regimes completos — ALTA, NEUTRO e sub-regimes, BAIXA, RECUPERACAO, PANICO
  - Q10 aberto: S6 VALE3 congelado 2024-Q1 — pode afetar classificacao de regime nesse periodo
  - Defasagem ORBIT monitorada pelo GATE EOD — defasagem 1m=MONITORAR, 2m+=BLOQUEADO
---
