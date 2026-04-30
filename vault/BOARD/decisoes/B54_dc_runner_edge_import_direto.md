---
uid: B54
title: dc_runner — eliminar subprocess, importar edge.py como módulo direto
status: closed
opened_at: 2026-04-14
closed_at: 2026-04-29
opened_in: [[BOARD/atas/2026-04-14_dc_runner_edge_fusao]]
closed_in: [[BOARD/atas/2026-04-29_fechamento_b53_b54_b55_b56_b57]]
decided_by: board
system: atlas

description: >
  dc_runner.py atualmente executa edge.py como processo filho via subprocess.Popen,
  comunicando via stdout e arquivo JSONL temporário. Arquitetura aprovada para migração:
  dc_runner.py passa a importar delta_chaos.edge como módulo Python e chamar funções
  diretamente. Eliminados: subprocess, JSONL, _watch_events_inner, _flush_events,
  _get_dc_script, variáveis de ambiente ATLAS_RUN_ID/PYTHONUNBUFFERED.
  Spec emitida por Lilian com adendos SCAN incorporados.

gatilho:
  - CEO entrega spec ao PLAN e implementação é concluída

impacted_modules:
  - atlas_backend/core/dc_runner.py
  - delta_chaos/edge.py

resolution: >
  Implementado. dc_runner.py importa delta_chaos.edge diretamente (linha 8).
  asyncio.to_thread() em uso em todos os wrappers assíncronos.
  rodar_backtest_dados() e rodar_orbit_update() removidas todas as chamadas
  emit_dc_event de ciclo de vida (11 + 8 chamadas removidas). dc_runner.py
  é o único emissor de dc_module_start e dc_module_complete. Bloco __main__
  em edge.py preservado intacto. Suite 76/76 verde. SCAN aprovado 2026-04-29.

notes:
  - SCAN adendo 1: emit_event → emit_dc_event com mapeamento start/done/error explícito
  - SCAN adendo 2: bloco __main__ em edge.py deve ser mantido
  - SCAN adendo 3: funções de edge.py são bloqueantes — asyncio.to_thread() obrigatório em todos os wrappers async
  - Polling SQLite para TUNE (_poll_sqlite) preservado intacto
  - REGRA ARQUITETURAL: dc_runner.py é a única autoridade para eventos de ciclo de vida
  - Exceção única: tune.py pode emitir dc_tune_progress (telemetria Optuna)
  - AUDITORIA SCAN 2026-04-29: APROVADO ✅
---
