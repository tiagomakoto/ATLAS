---
uid: B63
title: Renomeação NEUTRO_* → LATERAL_* e colapso de regimes esparsos
status: open
opened_at: 2026-04-29
closed_at:
opened_in: [[BOARD/atas/2026-04-29_regimes_nomenclatura_lateral]]
closed_in:
decided_by:
system: delta_chaos

description: >
  Os subregimes NEUTRO_* serão renomeados para LATERAL_* para refletir
  com mais precisão a identidade de mercado de cada estado. Dois regimes
  serão eliminados por insuficiência estatística estrutural e natureza
  metodológica. O universo de regimes passa de 10 para 7.

  Mapeamento aprovado pelo board:
    NEUTRO_BEAR      → LATERAL_BEAR   (renomear — 23% frequência média)
    NEUTRO_BULL      → LATERAL_BULL   (renomear — 20% frequência média)
    NEUTRO_LATERAL   → LATERAL        (renomear + absorver NEUTRO_MORTO)
    NEUTRO_MORTO     → colapsar em LATERAL (sizing=0 legado, N insuficiente)
    NEUTRO_TRANSICAO → eliminar       (artefato ORBIT, ~7% frequência constante)
    NEUTRO isolado   → eliminar       (chave fantasma, 0 ciclos em todos os ativos)

  Universo final: PANICO | BAIXA | LATERAL_BEAR | LATERAL | LATERAL_BULL |
                  ALTA | RECUPERACAO

  Dados empíricos que embasaram a decisão (ciclos históricos deduplicados):
    VALE3 (288): NEUTRO_BEAR=65, NEUTRO_BULL=62, NEUTRO_LATERAL=15,
                 NEUTRO_MORTO=17, NEUTRO_TRANSICAO=14
    PETR4 (288): NEUTRO_BEAR=70, NEUTRO_BULL=51, NEUTRO_LATERAL=14,
                 NEUTRO_MORTO=17, NEUTRO_TRANSICAO=24
    BOVA11(174): NEUTRO_BEAR=41, NEUTRO_BULL=36, NEUTRO_LATERAL=4,
                 NEUTRO_MORTO=9,  NEUTRO_TRANSICAO=15

  LATERAL combinado (NEUTRO_LATERAL + NEUTRO_MORTO):
    VALE3=32, PETR4=31, BOVA11=13 — BOVA11 permanece abaixo do threshold
    de calibração mas é aceitável dado histórico mais curto.

  NEUTRO_TRANSICAO: frequência constante ~7% independente do histórico —
  confirmado como artefato de fronteira do ORBIT, não regime de mercado.

  regimes_sizing no JSON é letra morta (B56 — decisão 2026-04-25).
  O que define operabilidade de um regime é estrategias[regime] != None.

gatilho:
  - CEO confirma T2 (confirmado em sessão 2026-04-29)
  - SPEC emitida por Lilian — implementação via Plan + Chan

impacted_modules:
  - orbit.py (classificação + critério redistribuição NEUTRO_TRANSICAO)
  - tune.py (chaves de regime em config + ranking)
  - fire.py (leitura de estrategias[regime])
  - gate.py (backtest por regime)
  - book.py (registro de trades por regime)
  - delta_chaos_config.json (candidatos por regime)
  - JSONs de todos os ativos (historico, estrategias, regimes_sizing a remover)
  - ATLAS frontend (labels de regime em todas as telas)

resolution:

notes:
  - Critério de redistribuição de NEUTRO_TRANSICAO precisa ser definido
    na SPEC — proposta: colapsar em LATERAL por default (regime mais neutro
    disponível) com fallback para regime anterior do ciclo se disponível.
  - regimes_sizing a ser removido dos JSONs nesta mesma migração (B56).
  - NEUTRO isolado (chave fantasma) a ser removido de estrategias[] e
    regimes_sizing[] de todos os ativos.
  - Blast radius equivalente a Q12 — SCAN obrigatório antes de merge.
  - PETR4 tinha 1125 ciclos duplicados (fator ~26x) — corrigido para 288
    antes desta deliberação. Origem do bug em orbit.py a investigar (B64).
  - Dependência: B56 (remoção regimes_sizing) pode ser executada
    conjuntamente nesta migração.
---
