---
date: 2026-04-12
session_type: off-ata
system: delta_chaos

decisions:
  # Diagnóstico e resolução de Q10
  - Campo regime_estrategia ausente em 518 ciclos históricos de todos os 4 ativos
    (VALE3, PETR4, BOVA11, BBAS3) — causa raiz identificada via investigação sequencial
  - Hipótese 1 (ORBIT não rodou) eliminada: 29 ciclos de VALE3 existem após 2024-Q1
  - Hipótese 2 (falha de escrita) eliminada: tape_ciclo_salvar salva dict completo sem filtragem
  - Causa raiz confirmada: regime_estrategia adicionado ao código após ciclos históricos
    já gravados; orbit_cache_carregar não re-processa ciclos existentes
  - Campo regime já continha sub-regimes corretos em todos os ciclos (NEUTRO_BULL etc.)
  - Solução 1 aplicada: script de migração retroativa popula regime_estrategia = regime
    nos 518 ciclos de todos os 4 ativos; escrita atômica via tempfile + os.replace
  - Solução 2 aplicada: indentação de regime_estrategia corrigida em orbit.py —
    ciclos futuros protegidos

tensoes_abertas:

tensoes_fechadas:
  - [[BOARD/decisoes/Q10_S6_VALE3_congelado]]

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]
  - [[SYSTEMS/delta_chaos/modules/TAPE]]

next_actions:
  - Avaliar Q11 (TUNE v1.1 VALE3 afetado por Q10) — agora que regime_estrategia
    está populado, verificar se TUNE de VALE3 precisa ser re-rodado
  - Commitar orbit.py com fix de indentação
---
