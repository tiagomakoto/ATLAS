---
uid: B54
title: dc_runner — eliminar subprocess, importar edge.py como módulo direto
status: open
opened_at: 2026-04-14
closed_at:
opened_in: [[BOARD/atas/2026-04-14_dc_runner_edge_fusao]]
closed_in:
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

resolution:

notes:
  - SCAN adendo 1: emit_event → emit_dc_event com mapeamento start/done/error explícito
  - SCAN adendo 2: bloco __main__ em edge.py deve ser mantido
  - SCAN adendo 3: funções de edge.py são bloqueantes — asyncio.to_thread() obrigatório em todos os wrappers async
  - Polling SQLite para TUNE (_poll_sqlite) preservado intacto
  - Estrutura de dc_calibracao_iniciar/_executar_calibracao_step1 preservada — apenas chamadas internas mudam
  - edge.py não é mais executado standalone fora do ATLAS (confirmado pelo CEO em sessão)
---
