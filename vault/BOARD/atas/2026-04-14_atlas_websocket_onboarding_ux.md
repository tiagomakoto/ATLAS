---
date: 2026-04-14
session_type: board
system: atlas

decisions:
  - Causa raiz do silêncio no frontend identificada e corrigida: emit_event de threads usava asyncio.run() criando loop isolado — corrigido com set_main_loop + call_soon_threadsafe em event_bus.py e main.py
  - edge.py e tune.py agora usam print(flush=True) sempre — nunca importam atlas_backend.terminal_stream (processo filho não tem acesso ao loop do uvicorn pai)
  - python -u e PYTHONUNBUFFERED=1 adicionados ao subprocess para flush imediato de stdout
  - dc_module_start reativado em _stream_subprocess — estava comentado, causando drawer sem sinal de início
  - dc_tune agora passa modulo="TUNE" — antes passava None, TUNE nunca emitia dc_module_start/complete
  - Bug dc_runner corrigido: bloco_mensal inicializado como None no ticker_digest — UnboundLocalError em dc_daily quando ciclo não mudou
  - OnboardingDrawer guard if(!onboarding) return null removido — impedia montagem do WebSocket antes do fetch completar
  - Drawer de onboarding confirmado funcional em uso real: PETR4 step 1 CONCLUÍDO visível com timestamp
  - Seis melhorias de UX/UI aprovadas pelo board com base em screenshot de uso real — B53 aberta
  - SPEC_ONBOARDING_DRAWER_UX_v1.0.md emitida por Lilian para PLAN do OpenCode

tensoes_abertas:
  - [[BOARD/tensoes_abertas/B53_onboarding_drawer_ux_melhorias]]

tensoes_fechadas:

impacted_modules:
  - atlas_backend/core/event_bus.py
  - atlas_backend/main.py
  - atlas_backend/core/dc_runner.py
  - delta_chaos/edge.py
  - delta_chaos/tune.py
  - atlas_ui/src/components/GestaoView/OnboardingDrawer.jsx

next_actions:
  - CEO entrega SPEC_ONBOARDING_DRAWER_UX_v1.0.md ao PLAN (B53)
  - Iniciar nova sessão — contexto desta conversa esgotado
---

# Ata — 2026-04-14 — ATLAS: WebSocket pipeline + OnboardingDrawer UX

## Contexto

Continuação da sessão 2026-04-13. Foco em debugging do pipeline de eventos WebSocket e melhorias de UX/UI do drawer de onboarding.

## Diagnóstico e correções do pipeline WebSocket

Sessão longa de debugging com múltiplas hipóteses testadas. Causa raiz final identificada em três camadas simultâneas:

**Camada 1 — Loop isolado (causa principal):**
`emit_event` chamado de threads (`_sync_runner` do dc_runner) caía no `except RuntimeError` do `asyncio.get_running_loop()` e executava `asyncio.run()` — criando loop novo e isolado, desconectado do `event_dispatcher` do uvicorn. Fix: `set_main_loop` guarda o loop do uvicorn no startup; `emit_event` usa `call_soon_threadsafe`.

**Camada 2 — Import do atlas_backend no subprocess:**
`edge.py` e `tune.py` importavam `atlas_backend.core.terminal_stream` com sucesso (PYTHONPATH incluía raiz do ATLAS), então `emit_log` chamava `emit_event` do processo filho — onde `_main_loop` é None. Eventos sumiam silenciosamente. Fix: ambos os módulos agora usam `print(flush=True)` diretamente.

**Camada 3 — dc_module_start comentado:**
O bloco que emitia `dc_module_start` antes do subprocess foi removido com comentário "causava duplicação". Sem ele, o drawer nunca recebia sinal de início de nenhum step. Fix: reativado. `dc_tune` também estava com `modulo=None` — corrigido para `modulo="TUNE"`.

**Bug adicional corrigido:**
`dc_daily` explodia com `UnboundLocalError: bloco_mensal` quando o ciclo não mudou — variável definida dentro do `if _ciclo_mudou()` mas referenciada fora. Fix: inicializar `bloco_mensal: None` no `ticker_digest`.

## Resultado confirmado

Screenshot de uso real mostra drawer de onboarding com:
- PETR4 step 1 (backtest_dados) CONCLUÍDO com timestamp 14/04/2026, 11:16:56
- Steps 2 e 3 PENDENTES

Canal WebSocket funcionando. Eventos chegando ao frontend.

## Melhorias de UX/UI aprovadas (B53)

Board identificou seis melhorias a partir do screenshot:
1. Bug de numeração nos steps do resumo do topo
2. Remover resumo redundante do topo
3. Nome técnico da etapa em cada card
4. Próximo step em azul sutil
5. Duração calculada no card concluído
6. Descrição prévia no card TUNE quando pendente

Lilian emitiu SPEC_ONBOARDING_DRAWER_UX_v1.0.md para PLAN.

## Tensões abertas desta sessão

- [[BOARD/tensoes_abertas/B53_onboarding_drawer_ux_melhorias]]
