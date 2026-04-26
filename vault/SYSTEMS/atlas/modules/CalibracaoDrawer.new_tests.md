---
uid: mod-atlas-027
version: 1.0.1
status: validated
owner: Chan | Lilian | Board

function: Testes de integração do CalibracaoDrawer — cobre renderização de critérios GATE, diagnóstico FIRE, painéis de sucesso/bloqueio, guard de frescor de dados e fetches fallback de API.
file: atlas_ui/src/components/GestaoView/__tests__/CalibracaoDrawer.new_tests.jsx
role: Suite de testes — valida comportamento do CalibracaoDrawer nos fluxos GATE+FIRE e guard/skip step 1.

input:
- CalibracaoDrawer: React component — componente sob teste
- WebSocket events: dict — eventos dc_module_complete simulados

output:
- 12 test cases — 9 para Step 3 GATE+FIRE, 3 para Guard e Skip Step 1

depends_on:
- [[SYSTEMS/atlas/modules/CalibracaoDrawer]]

depends_on_condition: []

used_by: []

intent:
- Garantir que o CalibracaoDrawer renderiza corretamente os estados GATE (aprovação/bloqueio), FIRE (diagnóstico por regime) e guard de frescor de dados cotahist.

constraints:
- 12 test cases total — 9 (Step 3 GATE+FIRE) + 3 (Guard/Skip Step 1)
- Usa jest.fn() para mockOnClose
- WebSocket simulado via require('../../hooks/useWebSocket')
- Verifica textos específicos: BLOQUEADO, CALIBRACAO CONCLUIDA, GATE BLOQUEADO, Dados atualizados, Pular step 1
- Testa fetches fallback para /ativos/{ticker}/gate-resultado e /ativos/{ticker}/fire-diagnostico

notes:
- 2026-04-17 — módulo criado automaticamente a partir de atlas_ui/src/components/GestaoView/__tests__/CalibracaoDrawer.new_tests.jsx
- 2026-04-25 — vault validado: campos BOARD_REVIEW_REQUIRED preenchidos via análise de código