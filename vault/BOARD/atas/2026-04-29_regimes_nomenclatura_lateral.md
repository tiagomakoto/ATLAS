---
date: 2026-04-29
session_type: board
system: delta_chaos

decisions:
  - id: D01
    o_que: Regimes NEUTRO_* renomeados para LATERAL_* — universo de 10 para 7 regimes
    porque: >
      "NEUTRO" implica ausência de regime. "LATERAL" implica regime com identidade
      própria. NEUTRO_BEAR/BULL têm frequência 20-24% e são regimes reais.
      NEUTRO_MORTO (sizing=0 legado, N insuficiente) colapsa em LATERAL.
      NEUTRO_TRANSICAO (~7% constante entre ativos) é artefato metodológico do
      ORBIT — o classificador dizendo "não sei" — não é regime de mercado.
      Dados empíricos de VALE3, PETR4 e BOVA11 confirmaram a decisão.
    rejeitado: >
      Manter 10 regimes — rejeitado. Três regimes estruturalmente vazios ou
      insuficientes criam falsa granularidade sem poder estatístico.

  - id: D02
    o_que: regimes_sizing no JSON é letra morta — operabilidade definida por estrategias[regime]
    porque: >
      B56 (2026-04-25) declarou regimes_sizing formalmente redundante com a
      arquitetura sizing_orbit × sizing_reflect. CEO confirmou: o que define
      se um regime opera é estrategias[regime] != None, não regimes_sizing.
      Campo será removido conjuntamente na migração B63.
    rejeitado: >
      Usar regimes_sizing como referência para deliberação T2 — rejeitado.
      Dado legado sem valor operacional.

  - id: D03
    o_que: PETR4 historico[] tinha 1125 entradas com 288 únicas — corrigido para 288
    porque: >
      Bug de append sem deduplicação em orbit.py multiplicou ciclos ~26x.
      Arquivo corrigido via deduplicação por data_ref antes da deliberação T2.
      Bug registrado como B64 para investigação da origem.
    rejeitado: >
      Usar dados contaminados de PETR4 para decisão de regime — rejeitado.
      Deliberação aguardou correção.

tensoes_abertas:
  - [[BOARD/tensoes_abertas/B63_regimes_renomeacao_lateral]]
  - [[BOARD/tensoes_abertas/B64_petr4_historico_duplicado_orbit]]

tensoes_fechadas: []

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]
  - [[SYSTEMS/delta_chaos/modules/BOOK]]
  - [[SYSTEMS/delta_chaos/config/delta_chaos_config.json]]

next_actions:
  - Lilian emite SPEC_REGIMES_MIGRACAO (B63)
  - Chan investiga origem do bug de duplicação em orbit.py (B64)
  - Verificar BBAS3 com script de diagnóstico de duplicatas
---

# Ata — 2026-04-29 — Regimes: nomenclatura LATERAL + migração

## Contexto
Sessão complementar ao TUNE v3.1. Análise de dados históricos por regime
revelou granularidade excessiva nos subregimes NEUTRO_*. Board deliberou
sobre renomeação, colapso e eliminação com base em distribuição empírica
de ciclos nos ativos qualificados. Bug de duplicação em PETR4 identificado
e corrigido antes da deliberação.

## Decisões

### D01 — Universo de regimes reduzido de 10 para 7
**O que:** NEUTRO_BEAR→LATERAL_BEAR, NEUTRO_BULL→LATERAL_BULL,
NEUTRO_LATERAL→LATERAL (absorve NEUTRO_MORTO), NEUTRO_TRANSICAO eliminado,
NEUTRO isolado eliminado.
**Por quê:** Dados empíricos confirmam três regimes estruturalmente insuficientes.
NEUTRO_TRANSICAO é artefato metodológico, não regime de mercado.
**Rejeitado:** Manter 10 regimes.

### D02 — regimes_sizing é letra morta
**O que:** Operabilidade definida exclusivamente por estrategias[regime] != None.
**Por quê:** B56 declarou campo redundante. CEO confirmou.
**Rejeitado:** Usar regimes_sizing como referência operacional.

### D03 — PETR4 corrigido de 1125 para 288 ciclos
**O que:** Bug de append sem deduplicação em orbit.py — fator ~26x. Corrigido.
**Por quê:** Dados contaminados não podem embasar decisão arquitetural.
**Rejeitado:** Deliberar com dados não verificados.

## Tensões abertas desta sessão
- [[BOARD/tensoes_abertas/B63_regimes_renomeacao_lateral]]
- [[BOARD/tensoes_abertas/B64_petr4_historico_duplicado_orbit]]

## Tensões fechadas desta sessão
Nenhuma.
