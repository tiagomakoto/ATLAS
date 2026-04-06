# event_bus.py não funciona em threads separadas

## Contexto
`emit_dc_event()` é chamado dentro de `_sync_runner()` no `dc_runner.py`, que roda via `asyncio.to_thread()` (thread separada).

## Problema
`emit_event()` tenta `asyncio.get_running_loop()` → falha (thread não tem loop rodando) → cai no `except RuntimeError: asyncio.run(publish_event(event))` → cria um **novo event loop isolado**. O `event_dispatcher` (no loop principal) nunca recebe o evento.

## Sintoma
Eventos `dc_module_start`, `dc_module_complete` etc. não chegam no WebSocket. O LogDrawer do frontend fica travado em "Iniciando...".

## Solução tentada (revertida)
Usar `run_coroutine_threadsafe()` com referência ao loop principal setada no startup. Funcionou mas causou outro bug e foi revertida.

## Status
⚠️ Aberto — o problema persiste. Eventos do orquestrador não chegam via WebSocket quando emitidos de threads.

## Arquivos relevantes
- `atlas_backend/core/event_bus.py`
- `atlas_backend/core/dc_runner.py`
- `atlas_backend/main.py`
