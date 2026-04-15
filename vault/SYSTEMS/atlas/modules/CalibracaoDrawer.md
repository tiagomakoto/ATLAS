---
uid: mod-atlas-022
version: 1.0.2
status: validated
owner: Chan

function: Drawer lateral para calibração (recalibração) de ativo existente. Dispara TUNE e exibe progresso de trials Optuna em tempo real via polling do SQLite, exibe relatório final para aprovação/rejeição pelo CEO.
file: atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx
role: Interface de calibração — recalibração de TP/STOP com feedback de progresso Optuna.

input:
  - ticker: str — ativo selecionado para calibração
  - Progresso via GET /delta-chaos/calibracao/{ticker}/progresso-tune

output:
  - DOM: drawer com barra de progresso de trials, melhor IR, e botões aplicar/rejeitar

depends_on:
  - [[SYSTEMS/atlas/modules/API_ROUTES]]

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/GestaoView]]

intent:
  - Exibir progresso granular do TUNE Optuna para que o CEO acompanhe em tempo real.

constraints:
  - Polling de progresso TUNE via endpoint dedicado (read-only SQLite)
  - Aplicação de parâmetros requer POST /delta-chaos/tune/aplicar com confirmação

notes:
  - 2026-04-14: código modificado — CalibracaoDrawer.jsx
---