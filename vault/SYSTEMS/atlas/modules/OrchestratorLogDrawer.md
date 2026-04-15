---
uid: mod-atlas-013
version: 1.0.1
status: validated
owner: Chan

function: Drawer de logs do Orquestrador com processamento de eventos estruturados do Delta Chaos. Exibe status dos módulos (GATE, XLSX, TP_STOP, TAPE, ORBIT, REFLECT) com ícones coloridos e barra de progresso em tempo real via WebSocket.
file: atlas_ui/src/components/OrchestratorLogDrawer.jsx
role: Drawer de logs em tempo real — feedback visual do ciclo de manutenção para o CEO.

input:
  - isRunning: bool — indica se o processo está ativo
  - isFinished: bool — indica se o processo terminou
  - drawerEvents: array — eventos fallback via props (quando WS não captura)

output:
  - DOM: drawer com cards de status por módulo, barra de progresso e mensagem em tempo real

depends_on:
  - [[SYSTEMS/atlas/modules/WEBSOCKET]]
  - [[SYSTEMS/atlas/modules/systemStore]]

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/UI_CORE]]

intent:
  - Substituir o parsing frágil de texto dos logs por processamento de eventos JSON estruturados do backend.

constraints:
  - MODULOS: GATE, XLSX EOD, TP/STOP, TAPE, ORBIT, REFLECT — ordem visual fixa
  - Conecta WebSocket em ws://localhost:8000/ws/events quando isRunning=true
  - Limpa moduloStatus e moduloAtual na transição false→true de isRunning
  - Limpa moduloStatus ao detectar "[DAILY] Processando" no terminal log (novo ativo no loop)
  - processarEventoDC processa dc_module_start, dc_module_complete, dc_module_error, dc_workflow_complete, daily_ativo_complete
  - Cores customizadas: XLSX erro=âmbar (não encontrado), TP_STOP erro=vermelho
  - Animação pulse CSS em módulos rodando e ticker ativo
  - Botão fechar só aparece quando isFinished=true

notes:
  - 2026-04-12 — módulo criado automaticamente a partir de atlas_ui/src/components/OrchestratorLogDrawer.jsx
  - WebSocket não fecha automaticamente quando isRunning fica false — removido para debug
---