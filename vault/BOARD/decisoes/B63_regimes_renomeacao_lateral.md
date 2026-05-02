---
uid: B63
title: Renomeação NEUTRO_* → LATERAL_* e colapso de regimes esparsos
status: closed
opened_at: 2026-04-29
closed_at: 2026-04-30
opened_in: [[BOARD/atas/2026-04-29_regimes_nomenclatura_lateral]]
closed_in: [[BOARD/atas/2026-04-30_b63_fechamento_regimes_lateral]]
decided_by: CEO
system: delta_chaos

description: >
  Os subregimes NEUTRO_* foram renomeados para LATERAL_* para refletir
  com mais precisão a identidade de mercado de cada estado. Dois regimes
  foram eliminados por insuficiência estatística estrutural e natureza
  metodológica. O universo de regimes passou de 10 para 7.

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

gatilho:
  - CEO confirmou T2 em sessão 2026-04-29
  - SPEC emitida por Lilian — implementada via patch cirúrgico Chan

impacted_modules:
  - orbit.py
  - tune.py
  - delta_chaos_config.json
  - JSONs dos ativos (tune_ranking_estrategia — hard reset planejado)

resolution:
  - orbit.py migrado: LATERAL_* em _classificar_sub_regime_lateral
    e _redistribuir_transicao. Confirmado por SCAN via leitura direta.
  - delta_chaos_config.json v1.4 — patch cirúrgico 2026-04-30:
      tune.candidatos_por_regime: 10 chaves NEUTRO_* → 7 chaves LATERAL_*
      tune.estrategia_estrutural_fixo: NEUTRO_MORTO removido (3 entradas)
      fire.regime_estrategia: 10 chaves → 7 chaves LATERAL_*
      fire.regimes_sizing_padrao: bloco removido (B56 — letra morta)
  - NEUTRO_* erradicado: 0 ocorrências — checklist CEO 2026-04-30 ✅ G Drive + Local.
  - Hard reset dos JSONs dos ativos: próxima ação operacional.
  - B56 executada conjuntamente nesta migração conforme previsto.

notes:
  - SCAN auditou orbit.py, tune.py e delta_chaos_config.json via MCP antes
    do fechamento. Mismatch orbit (migrado) vs config (não migrado) foi a
    causa raiz dos regimes antigos na tela de MGLU3.
  - tune_ranking_estrategia dos ativos existentes ainda contém chaves NEUTRO_*
    — não é bloqueador: o config é a fonte de verdade do TUNE. Hard reset resolve.
  - B38 (BOVA11 NEUTRO_TRANSICAO) obsoleta por esta decisão.
---
