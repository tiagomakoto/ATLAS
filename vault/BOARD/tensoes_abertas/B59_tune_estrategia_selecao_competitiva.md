---
uid: B59
title: TUNE v3.0 — seleção competitiva de estratégia por regime via Optuna
status: open
opened_at: 2026-04-25
closed_at:
opened_in: [[BOARD/atas/2026-04-25_tune_v3_eleicao_competitiva]]
closed_in:
decided_by: Board + CEO
system: delta_chaos

description: >
  O TUNE atualmente otimiza TP/STOP para uma estratégia fixa por regime
  (definida em cfg_ativo["estrategias"][regime] ou herdada do default em tape.py).
  Esta tensão registra a decisão de estender o TUNE para eleger a estratégia
  de forma competitiva: para cada regime com N ≥ estrategia_n_minimo trades
  históricos, rodar um study Optuna independente por candidato admissível e
  ranquear por IR. A estratégia eleita é confirmada pelo CEO antes de ser
  gravada no JSON do ativo.

  Decisões confirmadas:
  1. Escopo v3.0 = só estratégia. TP/STOP por regime fica para v3.1 (B61).
  2. Posições abertas: snapshot na entrada — confirmação v3.0 só afeta posições futuras.
  3. Candidatos admissíveis por regime definidos pelo CEO, persistidos em
     config.json — nunca hardcoded.
  4. N mínimo de trades = 15 (PE-008). Abaixo disso: candidato estrutural fixo
     sem eleição competitiva.
  5. Máscara REFLECT é global por regime — idêntica para todos os candidatos
     do mesmo regime (condição do ativo, não da estratégia).
  6. Ranking completo inescapável na UI — confirmação por regime, não global.
  7. Legacy deprecado na mesma entrega: executar_tune, tune_aplicar_estrategias,
     POST /tune/aplicar, TuneApprovalCard.jsx.

  Tabela de candidatos admissíveis (PE-008):
  ALTA:             [CSP, BULL_PUT_SPREAD]
  BAIXA:            [BEAR_CALL_SPREAD]          — estrutural fixo
  NEUTRO:           [BULL_PUT_SPREAD, CSP]
  NEUTRO_BULL:      [BULL_PUT_SPREAD, CSP]
  NEUTRO_BEAR:      [BEAR_CALL_SPREAD, BULL_PUT_SPREAD]
  NEUTRO_TRANSICAO: [BEAR_CALL_SPREAD, BULL_PUT_SPREAD]
  NEUTRO_LATERAL:   [BULL_PUT_SPREAD, BEAR_CALL_SPREAD]
  NEUTRO_MORTO:     []                          — bloqueado
  PANICO:           []                          — bloqueado
  RECUPERACAO:      [BULL_PUT_SPREAD]           — estrutural fixo

  Condições SCAN para início da Fase 3:
  C1: passo 6b adicionado — contingência se auditoria D12 (snapshot book.py) falhar.
  C2: dry-run mode no migration script (passo 11).
  C3: grep de NEUTRO em tune.py e fire.py documentado como checklist do passo 8.

gatilho:
  - implementação completa das 6 fases do plano TUNE v3.0
  - validação end-to-end: VALE3 (competitiva em vários regimes) + BBAS3
    (estrutural_fixo em pelo menos um regime)
  - SCAN re-audita e aprova

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]
  - [[SYSTEMS/atlas/modules/CalibracaoDrawer]]
  - [[SYSTEMS/atlas/modules/RELATORIOS]]

resolution:

notes:
  - Tabela de candidatos é provisória (PE-008) — revisão após acúmulo de dados
    de paper trading por regime.
  - NEUTRO legado (orbit.py:376/404/631/646/648/665) incluído em candidatos
    como ["BULL_PUT_SPREAD", "CSP"]. Consolidação NEUTRO ↔ NEUTRO_* é B60.
  - Snapshot D12: auditoria em book.py/fire.py:gerar_saidas obrigatória na
    Fase 3 antes de implementar. Se snapshot não garantido, corrigir antes
    de prosseguir (passo 6b do plano).
  - B61 a abrir: TUNE v3.1 — TP/STOP por regime + migração FIRE/GATE/BOOK.
  - Risco de tempo Optuna: ~30min por ativo com 100 trials × 12 studies.
    Mitigado por reuso de pré-computação (D4) e early stopping (patience=30).
---
