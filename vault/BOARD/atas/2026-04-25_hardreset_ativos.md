---
date: 2026-04-25
session_type: off-ata
system: delta_chaos

decisions:
  - id: D01
    o_que: Hard reset completo dos JSONs de todos os ativos (BBAS3, ITUB4, PETR4, VALE3, BOVA11, BBDC4, PRIO3)
    porque: >
      Diagnóstico revelou contaminação estrutural dos históricos: ITUB4 com 262 ciclo_ids
      duplicados (valores divergentes entre runs), PETR4 com 1.125 ciclos quando esperado ~288
      (até 26 cópias exatas do mesmo ciclo_id). Qualquer calibração feita sobre esses dados
      é suspeita. Adicionalmente, o único paper trade executado (B0001 BOVA11) foi sob TUNE v1.0,
      já obsoleto. Decisão do CEO: começar de zero com dados limpos.
    rejeitado: >
      Dedup cirúrgico de historico[] + reset de calibracao{} — descartado pois os parâmetros
      operacionais (TP/STOP, estrategias) derivados de calibrações sobre dados contaminados
      também são suspeitos. Hard reset é mais seguro e alinha com a transição para TUNE v3.0.

tensoes_abertas: []

tensoes_fechadas:
  - [[BOARD/decisoes/B60_neutro_consolidacao]]

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]

next_actions:
  - Executar hardreset_ativos.py no ambiente local (G:\Meu Drive\Delta Chaos\ativos)
  - Rodar onboarding completo para cada ativo (TUNE v3.0 → GATE → confirmar status)
  - Sequência recomendada: BBAS3 → VALE3 → PETR4 → BOVA11 → BBDC4 → PRIO3 → ITUB4 (aguarda set/2026)
---

# Ata — 2026-04-25 — Hard Reset Ativos

## Contexto
Diagnóstico dos JSONs dos ativos revelou contaminação por múltiplos backtests appended sem deduplicação.
PETR4 com 1.125 ciclos (esperado ~288), ITUB4 com 262 duplicatas com valores divergentes.
CEO decidiu por hard reset completo para iniciar paper trading real sob TUNE v3.0.

## Decisões

### D01 — Hard reset completo de todos os ativos
**O que:** Zerar `historico[]`, `historico_config[]`, `reflect_cycle_history{}`, `tune_ranking_estrategia{}`, `calibracao{}`, `estrategias{}`, `take_profit`, `stop_loss`, `status` → MONITORAR, campos REFLECT. Preservar apenas: `ativo`, `ticker`, `foco`, `externas`, `regimes_sizing`, `criado_em`.

**Por quê:** Dados de backtest acumulados de forma não-atômica produziram históricos corrompidos. PETR4 especialmente crítico: até 26 cópias do mesmo ciclo_id, anos 2021–2025 com excesso de 150–273 ciclos/ano. Qualquer TUNE ou GATE rodado sobre esses dados é inválido. O único paper trade real (B0001 BOVA11 / TUNE v1.0) é obsoleto — TUNE v3.0 é o modelo vigente.

**Rejeitado:** Dedup cirúrgico — parâmetros derivados de dados contaminados também são suspeitos; não compensa preservar.

### D02 — B60 fechado por diagnóstico
**O que:** NEUTRO genérico tem zero ocorrências em todos os ativos (BBAS3, ITUB4, PETR4, VALE3). O regime legado não aparece no histórico real — consolidação estrutural com NEUTRO_* é desnecessária.

**Por quê:** O gatilho de B60 era "diagnóstico de frequência de NEUTRO vs NEUTRO_*". O diagnóstico foi executado e o resultado é inequívoco: 0/288, 0/561, 0/1125, 0/288 ciclos com regime == "NEUTRO".

**Rejeitado:** Eliminar o código em orbit.py que pode gerar NEUTRO — decision: manter como está, simplesmente não ocorre na prática com os ativos do universo atual.

## Tensões fechadas desta sessão
- [[BOARD/decisoes/B60_neutro_consolidacao]]
