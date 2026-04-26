---
uid: B60
title: NEUTRO legado — consolidação com subregimes NEUTRO_*
status: closed
opened_at: 2026-04-25
closed_at: 2026-04-25
opened_in: [[BOARD/atas/2026-04-25_tune_v3_eleicao_competitiva]]
closed_in: [[BOARD/atas/2026-04-25_hardreset_ativos]]
decided_by: Board + CEO
system: delta_chaos

description: >
  O ORBIT produz "NEUTRO" como regime ativo em algumas condições de classificação
  (orbit.py:376/404/631/646/648/665). O sistema também opera com subregimes
  NEUTRO_BULL, NEUTRO_BEAR, NEUTRO_TRANSICAO, NEUTRO_LATERAL e NEUTRO_MORTO.
  A coexistência de "NEUTRO" genérico e subregimes específicos pode gerar
  inconsistências no FIRE, GATE e TUNE. Esta tensão registra a necessidade
  de consolidação — ou eliminação do NEUTRO genérico em favor dos subregimes.

  Decisão provisória (TUNE v3.0): incluir NEUTRO em candidatos_por_regime
  com ["BULL_PUT_SPREAD", "CSP"] para não bloquear o sistema durante a
  implementação. Consolidação estrutural fica para B60.

gatilho:
  - diagnóstico de frequência de NEUTRO vs NEUTRO_* no historico[] dos ativos
  - decisão do board: eliminar NEUTRO ou mantê-lo como regime válido

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]

resolution: >
  Diagnóstico executado em 2026-04-25 sobre os JSONs dos 4 ativos disponíveis.
  Resultado: NEUTRO genérico tem 0 ocorrências em todos os históricos
  (BBAS3: 0/288, ITUB4: 0/561, PETR4: 0/1125, VALE3: 0/288).
  O regime não ocorre na prática com o universo atual de ativos.
  Decisão: manter o código em orbit.py como está — sem consolidação necessária.
  NEUTRO permanece em candidatos_por_regime como salvaguarda para futuros ativos.

notes:
  - Identificado durante implementação do TUNE v3.0 (D11 do plano).
  - Escopo deliberadamente fora do v3.0 para não ampliar superfície da entrega.
  - Hard reset de 2026-04-25 invalida os dados analisados — mas a conclusão
    é robusta: NEUTRO não é produzido pelo ORBIT para os ativos do universo atual.
---
