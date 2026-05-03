---
uid: mod-delta-007
version: 1.1.19
status: validated
owner: Chan

function: Calibracao de TP e STOP por ativo via simulacao propria com proxy intradiario. Maximiza IR (razao de lucro) sobre janela historica valida. Nao usa FIRE internamente.
file: delta_chaos/tune.py
role: Calibrador de parametros operacionais — TP e STOP exclusivamente. Sizing e responsabilidade do REFLECT.

input:
  - ticker: str — codigo do ativo
  - master_json: dict — estado do ativo carregado pelo TAPE
  - cotahist: DataFrame — historico de opcoes para simulacao
  - anos_validos: list — janela de anos para calibracao

output:
  - tp_otimo: float — take profit calibrado
  - stop_otimo: float — stop loss calibrado (multiplo do premio)
  - ir_valido: float — IR na janela valida
  - resultado_breakdown: DataFrame — P&L por ano e regime

depends_on:
  - [[SYSTEMS/delta_chaos/modules/TAPE]]

depends_on_condition:

used_by:
  - [[SYSTEMS/delta_chaos/modules/GATE]]

intent:
  - Calibrar TP e STOP com robustez estatistica — janela valida evita lookahead.
  - TUNE calibra TP e STOP exclusivamente — sizing e responsabilidade do REFLECT.

constraints:
  - Metodo de proxy intradiario via minimo e maximo do dia
  - cfg_ativo sem take_profit/stop_loss durante loop — evita override do master JSON
  - STOP verificado antes do TP por conservadorismo
  - Simulacao propria — nao usa FIRE internamente
  - DELTA_ALVO_TUNE — renomeado para evitar conflito de escopo Colab com DELTA_ALVO do FIRE
  - Pinta celula pronta para aplicar TP/STOP ao final do screening

notes:
  - 2026-05-03: código modificado — tune.py
  - 2026-05-02: código modificado — tune.py
  - 2026-04-30: código modificado — tune.py
  - 2026-04-30: código modificado — tune.py
  - 2026-04-30: código modificado — tune.py
  - 2026-04-29: código modificado — tune.py
  - 2026-04-26: código modificado — tune.py
  - 2026-04-25: código modificado — tune.py
  - 2026-04-22: código modificado — tune.py
  - 2026-04-22: código modificado — tune.py
  - 2026-04-17: código modificado — tune.py
  - 2026-04-16: código modificado — tune.py
  - 2026-04-16: código modificado — tune.py
  - 2026-04-15: código modificado — tune.py
  - 2026-04-15: código modificado — tune.py
  - 2026-04-14: código modificado — tune.py
  - 2026-04-14: código modificado — tune.py
  - 2026-04-13: código modificado — tune.py
  - 2026-04-13: código modificado — tune.py
  - VALE3 — TP=0.90 STOP=2.0 — IR valido +4.211 (2019-2025) — 63 trades, 2 stops, 4 regimes
  - PETR4 — TP=0.90 STOP=2.0 — IR valido +2.931 — 24 trades validos, STOP=1.5x inoperavel
  - BOVA11 — TP=0.75 STOP=1.5 — IR valido +5.198 — 67 trades validos, 2 stops
  - B26 aberto: divergencia GATE vs TUNE em VALE3 — GATE sugere TP=0.75 STOP=1.0x
  - B37 aberto: BOVA11 baseline com P&L absoluto superior — monitorar em paper
  - B30 aberto: TUNE v2.0 precisa de mascara REFLECT e dimensao de estrategias por regime
  - B42 aberto: TUNE v2.0 — quatro correcoes pendentes antes de rodar em producao
  - Q11 aberto: TUNE v1.1 VALE3 potencialmente afetado por Q10 (S6 congelado 3 ciclos)
  - Sequencia obrigatoria pre-capital real: REFLECT no EDGE -> reprocessar backtest -> retunar
---
