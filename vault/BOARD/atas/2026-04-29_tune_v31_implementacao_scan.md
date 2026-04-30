---
date: 2026-04-29
session_type: board
system: delta_chaos

decisions:
  - id: D01
    o_que: TUNE v3.1 aprovado por SCAN — merge liberado
    porque: >
      SCAN auditou tune.py e router delta_chaos.py. Dois bloqueadores
      identificados: H1 (sizing_config bloqueando simulação silenciosamente)
      e A1 (endpoint antigo sem 410). H1 corrigido via patch cirúrgico.
      A1 e A2 confirmados resolvidos no router. H2 confirmado falso positivo.
      Zero referências residuais a sizing_config/_reg_sizing após patch.
    rejeitado: >
      Merge antes da auditoria SCAN — regra inviolável do board.

  - id: D02
    o_que: sizing_config e _reg_sizing removidos de _simular_para_candidato
    porque: >
      regimes_sizing é letra morta (B56 — 2026-04-25). A condição
      sizing_config <= 0.0 bloqueava silenciosamente regimes como
      NEUTRO_MORTO, NEUTRO_TRANSICAO, RECUPERACAO, BAIXA, PANICO —
      N=0 nesses regimes era artefato do bug, não ausência de edge.
      Guarda correta: sizing_orbit <= 0.0 apenas.
    rejeitado: >
      Manter sizing_config com valor fixo 1.0 — campo removido do sistema.

  - id: D03
    o_que: UX frontend — três estados visuais distintos para resultados TUNE v3.1
    porque: >
      Estados atuais ("ESTRUTURAL" em laranja) não comunicam semântica útil.
      Taleb identificou risco cognitivo: CEO pode confundir estrutural_fixo
      com calibrado. Douglas reforçou: complexidade operacional é custo real.
      Três estados: CALIBRADO (verde), FALLBACK (amarelo), ANOMALIA (vermelho),
      BLOQUEADO (cinza). Progresso de acúmulo N por regime em FALLBACK.
    rejeitado: >
      Manter confirmação manual por regime — compliance theater, substituído
      por aplicação automática com gate de anomalia (D05 da sessão anterior).

  - id: D04
    o_que: Drawer — barra de indexação e linha de trials são mutuamente exclusivas
    porque: >
      Durante indexação, "0/150 trials IR: 0.000" não tem valor e confunde.
      Cada fase (indexando / eleicao_A / calibracao_B) exibe apenas seus
      próprios indicadores de progresso.
    rejeitado: >
      Exibir ambos simultaneamente — gera ruído visual sem informação adicional.

tensoes_abertas:
  - [[BOARD/tensoes_abertas/B61_tune_v31_tp_stop_por_regime]]
  - [[BOARD/tensoes_abertas/B62_tune_grid_stop_range_revisao]]
  - [[BOARD/tensoes_abertas/B64_petr4_historico_duplicado_orbit]]

tensoes_fechadas:
  - [[BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva]]

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/atlas/api/routes/delta_chaos]]
  - [[SYSTEMS/atlas/modules/CalibracaoDrawer]]

next_actions:
  - Coder aplica SPEC_FRONTEND_TUNE_v31 (PR separado — confirmado CEO)
  - Chan investiga origem bug duplicação em orbit.py (B64 — prioridade imediata)
  - BBAS3 verificar duplicatas com script diagnóstico
  - B63 aguarda SPEC de migração (Lilian emite quando CEO confirmar sequência)
---

# Ata — 2026-04-29 — TUNE v3.1 implementação + SCAN + frontend SPEC

## Contexto
Sessão de implementação e auditoria do TUNE v3.1. Chan auditou código
pós-implementação via SCAN. Patch H1 aplicado e verificado. Router
auditado. SPEC frontend emitida por Lilian. Merge liberado por SCAN.

## Decisões

### D01 — TUNE v3.1 aprovado por SCAN — merge liberado
**O que:** tune.py v3.1 aprovado. Dois bloqueadores corrigidos (H1 patch,
A1/A2 já no router). Zero referências residuais a sizing_config.
**Por quê:** Regra inviolável — nenhuma versão de código aprovada sem SCAN.
**Rejeitado:** Merge pré-auditoria.

### D02 — sizing_config removido de _simular_para_candidato
**O que:** Guarda simplificada para `sizing_orbit <= 0.0`. Fórmula de n
usa apenas sizing_orbit.
**Por quê:** regimes_sizing é letra morta (B56). Bug silenciava N em
múltiplos regimes operáveis.
**Rejeitado:** Manter com valor fixo 1.0.

### D03 — Três estados visuais distintos para resultados TUNE v3.1
**O que:** CALIBRADO / FALLBACK / ANOMALIA / BLOQUEADO com cores,
ícones e semântica distintos. Progresso de acúmulo N em FALLBACK.
**Por quê:** "ESTRUTURAL" em laranja não comunica estado real.
Risco cognitivo de confundir fallback com calibrado.
**Rejeitado:** Manter confirmação manual por regime.

### D04 — Barra de indexação e linha de trials mutuamente exclusivas
**O que:** Cada fase exibe apenas seus próprios indicadores.
"0/150 trials IR: 0.000" não aparece durante indexação.
**Por quê:** Ruído visual sem valor durante fase de indexação.
**Rejeitado:** Exibição simultânea.

## Tensões abertas desta sessão
- [[BOARD/tensoes_abertas/B61_tune_v31_tp_stop_por_regime]]
- [[BOARD/tensoes_abertas/B62_tune_grid_stop_range_revisao]]
- [[BOARD/tensoes_abertas/B64_petr4_historico_duplicado_orbit]]

## Tensões fechadas desta sessão
- [[BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva]] — TUNE v3.0→v3.1 implementado e aprovado por SCAN
