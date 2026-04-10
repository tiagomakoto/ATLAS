---
date: 2026-03-23
session_type: board
system: delta_chaos

decisions:
  - PETR4 — GATE v1.0 — 8/8 — OPERAR — TP=0.90 STOP=2.0
  - BOVA11 — GATE v1.0 — 8/8 — OPERAR — TP=0.75 STOP=1.5
  - BOVA11 NEUTRO_BULL bloqueado — edge ausente
  - Paper trading iniciado — 2026-03-23
  - B0001 BOVA11 BEAR_CALL_SPREAD aberto — NEUTRO_BEAR | 113 contratos | prêmio R$1.52 | delta -0.29 | venc 2026-04-24
  - REFLECT confirmado passivo — não impactou backtests
  - VOL_FIN_MIN removido — volume > 0 em produção
  - _montar_bear_call corrigido — strike vendida < comprada
  - tape_paper() compatível com formato opcoes.net.br
  - Protocolo operacional: XLSX filtrado por vencimento mensal
  - Derman com mandato novo: premissas implícitas antes de aprovações

tensoes_abertas:
  - [[BOARD/tensoes_abertas/B35_REFLECT_backtest]]
  - [[BOARD/tensoes_abertas/B38_BOVA11_NEUTRO_TRANSICAO]]
  - [[BOARD/tensoes_abertas/B41_delta_alvo_fixo]]
  - [[BOARD/tensoes_abertas/B42_TUNE_v2]]
  - [[BOARD/tensoes_abertas/B44_preferencia_mensal_FIRE]]
  - [[BOARD/tensoes_abertas/B45_exercicio_antecipado]]
  - [[BOARD/tensoes_abertas/Q10_S6_VALE3_congelado]]
  - [[BOARD/tensoes_abertas/Q11_TUNE_VALE3_afetado_Q10]]

tensoes_fechadas:

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TAPE]]
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/delta_chaos/modules/BOOK]]
  - [[SYSTEMS/delta_chaos/modules/EDGE]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]

next_actions:
  - Monitorar B0001 — verificar slippage real de execução
  - Definir estratégia BOVA11 NEUTRO_TRANSICAO (B38)
  - Investigar Q10 — S6 VALE3 congelado 2024-Q1
  - Avaliar pilares B14 — capital segregado e protocolo operacional
---
