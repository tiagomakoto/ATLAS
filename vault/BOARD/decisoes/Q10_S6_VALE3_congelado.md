---
uid: Q10
title: S6 VALE3 congelado desde 2024-Q1
status: closed
opened_at: 2026-03-23
closed_at: 2026-04-12
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in: [[BOARD/atas/2026-04-12_Q10_regime_estrategia]]
decided_by: CEO
system: delta_chaos

description: >
  O campo regime_estrategia de VALE3 estava ausente em todos os ciclos históricos.
  Causa desconhecida na abertura. Poderia indicar falha na atualização do master JSON,
  problema na TAPE ou dado corrompido na fonte.

gatilho:
  - investigação imediata — próxima sessão

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TAPE]]
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]

resolution:
  - Causa raiz: campo regime_estrategia adicionado ao dict de retorno de
    orbit_ativo_processar após os 518 ciclos históricos já terem sido gravados.
    orbit_cache_carregar não re-processa ciclos existentes — campo nunca foi
    escrito nos JSONs históricos de nenhum dos 4 ativos.
  - Campo regime já continha os sub-regimes corretos (NEUTRO_BULL, NEUTRO_BEAR
    etc.) em todos os ciclos — migração retroativa trivial.
  - Solução 1: script de migração popula regime_estrategia = regime nos 518
    ciclos de VALE3, PETR4, BOVA11 e BBAS3. Escrita atômica via tempfile + os.replace.
  - Solução 2: indentação de regime_estrategia no dict de retorno de
    orbit_ativo_processar corrigida em orbit.py — ciclos futuros protegidos.

notes:
  - Q11 depende da resolução de Q10 — avaliar impacto em Q11
  - VALE3 operacional nos demais campos durante toda a tensão
  - Todos os 4 ativos foram afetados e migrados (não apenas VALE3)
---
