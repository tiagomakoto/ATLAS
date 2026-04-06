# LogDrawer trava em "Iniciando..."

## Contexto
O `OrchestratorLogDrawer.jsx` fica preso em "Iniciando..." durante a execução do orquestrador.

## Causas identificadas

### 1. useEffect com dependência `visible` (corrigido)
Adicionar `visible` nas dependências do `useEffect` fazia o cleanup rodar toda vez que `visible` mudava → desconectava o WebSocket logo após conectar.

**Fix:** Remover `visible` das dependências.

### 2. Drawer não reagia a eventos do orquestrador (corrigido)
O LogDrawer só processava eventos `dc_*` (dc_module_start, dc_module_complete). Eventos como `orchestrator_ativo_result` e `status_transition` caíam no void.

**Fix:** Adicionar handlers para `orchestrator_ativo_result`, `status_transition` e fallback para texto puro.

### 3. Botão "Verificando..." não voltava a "Check Status" (corrigido)
`orchestratorAtivo` no store nunca voltava a `false` porque `orchestrator_done` só era emitido no formato antigo (com `data.digest`). O novo formato com `data.eventos` não emitia o evento de conclusão.

**Fix:** Emitir `orchestrator_done` sempre que a resposta HTTP chega com sucesso.

## Arquivos
- `atlas_ui/src/components/OrchestratorLogDrawer.jsx`
- `atlas_ui/src/layouts/MainScreen.jsx`
- `atlas_ui/src/store/systemStore.js`

## Status
✅ Resolvido.
