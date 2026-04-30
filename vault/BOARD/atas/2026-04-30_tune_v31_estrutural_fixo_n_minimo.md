---
date: 2026-04-30
session_type: board
system: delta_chaos

decisions:
  - id: D01
    o_que: Mapeamento de estratégias estrutural_fixo para todos os regimes
    porque: TUNE v3.1 exige estratégia padrão para regimes sem trades suficientes para calibração. BAIXA e RECUPERACAO já estavam definidos; ALTA, LATERAL_BULL, LATERAL_BEAR e LATERAL estavam ausentes.
    rejeitado: Nenhuma alternativa formal considerada — board convergiu na lógica viés direcional → estrutura de spread.

  - id: D02
    o_que: N_MINIMO=20 é empírico — critério unidimensional insuficiente
    porque: Board identificou que volume de trades sem dispersão temporal é critério fraco. Concentração em evento único (ex. COVID 2020) invalida a amostra independente do tamanho.
    rejeitado: Revisão imediata do threshold — board decidiu manter 20 e registrar tensão para calibração pós paper trading com dados reais.

tensoes_abertas:
  - [[BOARD/tensoes_abertas/B66_n_minimo_grid_criterio_bidimensional]]

tensoes_fechadas: []

impacted_modules:
  - TUNE (estrutural_fixo, N_MINIMO)

next_actions:
  - Incorporar mapeamento D01 ao delta_chaos_config.json (estrutural_fixo por regime)
  - B66 revisão após 1º trimestre paper trading com dados reais
---

# Ata — 2026-04-30 — TUNE v3.1: estrutural_fixo por regime + N_MINIMO

## Contexto
Sessão motivada por duas lacunas no TUNE v3.1: (1) regimes ALTA, LATERAL_BULL, LATERAL_BEAR e LATERAL sem estratégia estrutural_fixo definida; (2) questionamento sobre o critério N_MINIMO=20 para acesso ao grid competitivo — origem empírica, não derivada formalmente.

## Decisões

### D01 — Mapeamento completo de estratégias estrutural_fixo por regime

**O que:**
| Regime | estratural_fixo |
|---|---|
| BAIXA | BEAR_CALL_SPREAD |
| RECUPERACAO | BULL_PUT_SPREAD |
| ALTA | BULL_PUT_SPREAD |
| LATERAL_BULL | BULL_PUT_SPREAD |
| LATERAL_BEAR | BEAR_CALL_SPREAD |
| LATERAL | BULL_PUT_SPREAD |
| PANICO | null |

**Por quê:** Lógica unificada por viés direcional — viés bull ou neutro → BULL_PUT_SPREAD; viés bear → BEAR_CALL_SPREAD. Em LATERAL, o skew estrutural do mercado BR penaliza mais o lado Put, favorecendo venda de downside via BULL_PUT_SPREAD.

**Rejeitado:** Nenhuma alternativa considerada — convergência do board sem dissidência na lógica direcional.

### D02 — N_MINIMO=20 mantido; tensão aberta para critério bidimensional

**O que:** N_MINIMO=20 permanece operacional. Tensão B66 aberta para revisão após dados reais de paper trading.

**Por quê:** Board identificou três problemas com o critério atual: (a) origem empírica, sem derivação formal para este sistema; (b) ambiguidade de direção — 20 pode ser permissivo demais para Optuna com 9 graus de liberdade (risco de overfitting) ou conservador demais para regimes raros; (c) critério unidimensional — volume sem dispersão temporal é insuficiente. Proposta de Thorp: adicionar `N_anos_com_trades ≥ 2` como segundo eixo.

**Rejeitado:** Revisão imediata — board entendeu que dados reais de paper trading devem informar a calibração.

## Tensões abertas desta sessão
- [[BOARD/tensoes_abertas/B66_n_minimo_grid_criterio_bidimensional]]
