---
date: 2026-04-29
session_type: board
system: atlas

decisions:
  - id: D01
    o_que: SPEC_FRONTEND_TUNE_v31 aprovada por SCAN — merge liberado com ressalva
    porque: >
      SCAN auditou CalibracaoDrawer.jsx e TuneRankingPanel.jsx.
      Todas as 4 adendas implementadas corretamente.
    rejeitado: >
      Merge sem auditoria SCAN — regra inviolável.

  - id: D02
    o_que: Ressalva SCAN — contrato body?.regime_dados?.status_calibracao pendente
    porque: >
      Path de leitura de statusCalibRetornado dependia de estrutura exata do
      response body — registrada como verificação obrigatória pré-deploy.
    rejeitado: >
      Ignorar ressalva.

  - id: D03
    o_que: Fix TuneRankingPanel — path corrigido para body?.status_calibracao (campo raiz)
    porque: >
      Ressalva SCAN D02 confirmada: router retorna status_calibracao no campo raiz,
      não aninhado em regime_dados. Path corrigido de
      body?.regime_dados?.status_calibracao para body?.status_calibracao.
      Contrato documentado inline:
      { status, ticker, regime, acao, estrategia, status_calibracao }.
      Badge 🟢/🟡 agora só aparece quando backend realmente retorna
      "calibrado" ou "fallback_global". Merge liberado sem restrições.
    rejeitado: >
      Manter path aninhado — contrato real do router é campo raiz.

tensoes_abertas:
  - [[BOARD/tensoes_abertas/B61_tune_v31_tp_stop_por_regime]]
  - [[BOARD/tensoes_abertas/B62_tune_grid_stop_range_revisao]]
  - [[BOARD/tensoes_abertas/B63_regimes_renomeacao_lateral]]
  - [[BOARD/tensoes_abertas/B64_petr4_historico_duplicado_orbit]]

tensoes_fechadas:
  - [[BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva]]

impacted_modules:
  - [[SYSTEMS/atlas/modules/CalibracaoDrawer]]
  - [[SYSTEMS/atlas/modules/TuneRankingPanel]]

next_actions:
  - Chan investiga origem bug duplicação orbit.py (B64 — prioridade imediata)
  - BBAS3 verificar duplicatas com script diagnóstico
  - B63 SPEC migração NEUTRO_*→LATERAL_* quando CEO confirmar sequência
---

# Ata — 2026-04-29 — SCAN frontend TUNE v3.1 + adendas aprovadas + fix router

## Contexto
SCAN auditou implementação das 4 adendas da SPEC_FRONTEND_TUNE_v31.
Ressalva de contrato de API identificada, fix aplicado na mesma sessão.
Merge liberado sem restrições ao final do dia.

## Decisões

### D01 — SPEC_FRONTEND_TUNE_v31 aprovada por SCAN
**O que:** Adendas #1–#4 implementadas. Merge liberado com ressalva.
**Por quê:** 10 itens auditados aprovados. Zero referências a endpoints
deprecados. ir_eleicao_mediana fora do drawer. Estados visuais pós-resolução
corretos. run_id no state funcional.
**Rejeitado:** Merge sem auditoria.

### D02 — Ressalva: contrato body?.regime_dados?.status_calibracao
**O que:** Path de leitura pendente de verificação. Não bloqueou merge.
**Por quê:** Estrutura exata do response body não confirmada.
**Rejeitado:** Ignorar ressalva.

### D03 — Fix: path corrigido para body?.status_calibracao
**O que:** Router retorna status_calibracao no campo raiz. Path corrigido.
Contrato documentado inline. Badge 🟢/🟡 funcionando corretamente.
Merge liberado sem restrições.
**Rejeitado:** Manter path aninhado.

## Tensões fechadas desta sessão
- [[BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva]] — TUNE v3.1 backend + frontend completos, SCAN aprovado, merge liberado sem restrições
