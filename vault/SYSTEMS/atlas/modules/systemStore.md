---
uid: mod-atlas-014
version: 1.0.3
status: validated
owner: Chan

function: Store global de estado (Zustand) para a SPA ATLAS. Centraliza health, módulos DC, ciclo, eventos, digest por ativo, ativos parametrizados e progresso TUNE. Atualiza estado via updateFromEvent processando eventos WebSocket tipados.
file: atlas_ui/src/store/systemStore.js
role: Centralizador de estado da UI — único ponto de state management para componentes React.

input:
  - event: dict — evento tipado recebido via WebSocket (type + data)

output:
  - state: objeto reativo Zustand — consumido por hooks React em componentes

depends_on:
  - [[SYSTEMS/atlas/modules/WEBSOCKET]]

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/UI_CORE]]

intent:
  - Ser a fonte única de estado da UI. Nenhum componente armazena estado crítico localmente.
  - Store é event-driven — atualiza via switch/case sobre event.type recebido do WebSocket.

constraints:
  - Zustand via create() — sem providers, consumo direto via useSystemStore hook
  - Eventos tipados suportados: health_update, health, dc_module_start, dc_module_complete, cycle_update, event, regime_update, alert, daily_start, daily_progress, daily_done, daily_error, status_transition, daily_ativo_complete, ativos_parametrizados_loaded, daily_ativo_updated, TUNE (trial)
  - daily_start limpa modules, digestPorAtivo, statusTransitions e ativosParametrizados
  - daily_ativo_updated faz upsert no array ativosParametrizados por ticker
  - dc_module_start/complete indexa por ticker (ou "global") no objeto modules
  - events mantém buffer circular de 50 itens
  - tuneProgress armazena ticker, trialNumber, trialsTotal, bestIr, semMelhoria

notes:
  - Campos de estado: health, health_reason, modules, cycle, events, regime, alert, dailyAtivo, dailyConcluido, progresso, digestItems, digestTimestamp, digestPorAtivo, cicloNovo, statusTransitions, ativosParametrizados, tuneProgress
---