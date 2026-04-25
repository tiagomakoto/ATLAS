---
uid: B56
title: REFLECT — sizing por estado A/B/C/D/X e eliminação de regimes_sizing do JSON
status: open
opened_at: 2026-04-24
closed_at:
opened_in: [[BOARD/atas/2026-04-24_reflect_estados_sizing]]
closed_in:
decided_by: Board + CEO
system: delta_chaos

description: >
  Duas decisões de design aprovadas em 2026-04-24:

  1. SIZING POR ESTADO REFLECT (canônico):
     O sizing do sistema é determinado exclusivamente pelo estado REFLECT
     e pelo ORBIT (via IR). O campo regimes_sizing no JSON do ativo é
     redundante — o ORBIT já bloqueia via IR quando edge é insuficiente,
     e o REFLECT modula o sizing final. A tabela canônica aprovada é:

       A → sizing_orbit × (1.0 + alpha)   [alpha via B01/B29]
       B → sizing_orbit × 1.0
       C → sizing_orbit × 0.5             [PE-007 — provisório]
       D → sizing_orbit × 0.0
       T → sizing_orbit × 0.0 + protocolo [B02] (Tail)

     Quando estratégia não está configurada para o regime → sizing = 0.0
     (bloqueio via FIRE, independente de REFLECT).

  2. REGIMES_SIZING NO JSON É FORMALMENTE REDUNDANTE — REMOVER:
     Com a arquitetura aprovada (sizing_orbit binário × sizing_reflect
     por estado A/B/C/D/T), o campo regimes_sizing no JSON do ativo
     nunca entra na equação de sizing_final. O ORBIT passa a ser
     genuinamente binário: IR > threshold → 1.0, senão → 0.0.
     O campo é letra morta e deve ser removido.

     Sequência obrigatória de remoção (Thorp):
       (1) Corrigir ORBIT para ser genuinamente binário — ignorar
           regimes_sizing do JSON, retornar 1.0 ou 0.0 via IR puro.
       (2) Remover campo regimes_sizing dos JSONs de todos os ativos.
       (3) Remover leitura do campo em tape_ativo_inicializar() e
           tape_ativo_carregar() — limpar defaults e migração.

  3. DADOS EMPÍRICOS QUE SUPORTAM C = 0.5:
     Análise de 5 ativos (BBAS3, BOVA11, ITUB4, PETR4, PRIO3):
     - 20 ciclos C identificados
     - 90% reverteram para A ou B no ciclo seguinte (C é majoritariamente transitório)
     - 0% precederam D ou X
     - 75% tinham IR positivo no próprio ciclo C
     - 45% tinham sizing ORBIT > 0 (ORBIT autorizava operação)
     Conclusão: C = 0.0 desperdiçaria edge em 90% dos casos.
     C = 0.5 é conservadorismo calibrado, não parada completa.
     Amostra insuficiente (20 obs) para calibração precisa — valor é PE-007.

gatilho:
  - implementação: reflect_sizing_calcular() deve usar lookup por estado
    em vez de fórmula linear sobre score numérico
  - default regimes_sizing = 1.0 para todos os regimes com estratégia ativa
  - calibração de C via B30 (TUNE com máscara reflect_state) quando disponível
  - B04 (thresholds) precisa ser resolvido antes de calibrar C com precisão

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]
  - [[SYSTEMS/delta_chaos/modules/EDGE]]
  - [[SYSTEMS/delta_chaos/modules/TAPE]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]

resolution:

notes:
  - PE-007: sizing C = 0.5 — provisório. Limitação: 20 ciclos observados em
    5 ativos. Condição de revisão: B30 implementado + mínimo 50 ciclos C
    observados com estratégia ativa.
  - D = 0.0 e T = 0.0 têm sizing idêntico mas semântica diferente:
    D é "edge ausente agora", T é "evento estrutural, verificar antes de voltar" (Tail).
  - regimes_sizing no JSON é formalmente redundante e deve ser removido
    em duas etapas: (1) ORBIT binário puro via IR, (2) remoção do campo
    dos JSONs e do código de tape.py.
  - Relacionado: B55 (redesign estados), B01 (alpha A), B29 (condição Taleb),
    B04 (thresholds), B30 (TUNE máscara REFLECT).
---
