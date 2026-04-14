---
uid: Q12
title: regime_estrategia renomeado para regime — padronização global
status: closed
opened_at: 2026-04-13
closed_at: 2026-04-13
opened_in: [[BOARD/atas/2026-04-13_regime_padronizacao]]
closed_in: [[BOARD/atas/2026-04-13_regime_padronizacao]]
decided_by: CEO
system: delta_chaos

description: >
  Durante onboarding de PRIO3 e BBDC4, ORBIT v3.6 passou a retornar
  KeyError 'regime' ao tentar acessar campo inexistente no dict de resultado
  de orbit_ativo_processar. Causa raiz: campo foi renomeado para
  regime_estrategia em orbit.py mas os consumidores (edge.py, gate.py,
  fire.py, tape.py) continuaram esperando 'regime'. Renomeação foi
  incompleta e inconsistente. Adicionalmente, o board deliberou sobre
  a intenção semântica original do nome regime_estrategia — se antecipava
  múltiplas estratégias por regime no futuro.

gatilho:
  - ORBIT erro: 'regime' em runtime — PRIO3 e BBDC4
  - Pergunta do CEO: havia intenção de múltiplas estratégias por regime?

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]
  - [[SYSTEMS/delta_chaos/modules/EDGE]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]
  - [[SYSTEMS/delta_chaos/modules/TAPE]]

resolution: >
  Deliberação do board: regime_estrategia tinha fundamento conceitual
  (antecipar divergência regime→estratégia), mas o valor armazenado
  sempre foi o nome do regime ('ALTA', 'NEUTRO_BULL'), não da estratégia
  ('CSP', 'BULL_PUT_SPREAD'). Mapeamento 1:1 no código. Campo correto
  é 'regime'. Expansão futura (múltiplas estratégias por regime) pertence
  ao dict 'estrategias' no master JSON — que já é 1:N por design.

  Ações executadas:
  1. orbit.py: "regime_estrategia" → "regime" no dict de retorno de
     orbit_ativo_processar. Único ponto de produção do campo.
  2. migrate_regime.py: script de migração atômica (tempfile + os.replace)
     executado com sucesso.
  3. Resultado da migração:
     - BBAS3.json:  288/288 ciclos migrados
     - BBDC4.json:   14/190 ciclos migrados (14 novos, 176 já corretos)
     - BOVA11.json: 160/160 ciclos migrados
     - ITUB4.json:    0 ciclos (já correto — sem regime_estrategia)
     - PETR4.json: 1125/1125 ciclos migrados
     - PRIO3.json:   14/156 ciclos migrados (14 novos, 142 já corretos)
     - VALE3.json:  518/518 ciclos migrados
     - Total: 2119 ciclos normalizados em 7 arquivos
  4. Backups criados com sufixo .bak_<timestamp> para todos os arquivos
     modificados.

notes:
  - ITUB4 já estava correto pois nunca passou pelo período com regime_estrategia
  - BBDC4 e PRIO3 com migração parcial (14 ciclos cada) confirmam que
    o erro era recente — apenas ciclos gerados após a renomeação incorreta
  - O dict 'estrategias' no master JSON permanece inalterado — é o lugar
    correto para expansão futura de mapeamento regime→estratégia
  - Relacionado a Q10 (mesmo padrão de problema: campo ausente em historico[])
---
