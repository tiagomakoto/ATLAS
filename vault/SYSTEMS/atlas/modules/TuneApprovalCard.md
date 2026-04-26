---
uid: mod-atlas-048
version: 1.0.1
status: validated
owner: Chan
function: Card de aprovação TUNE — exibe TP/STOP sugerido vs atual, com botões Aplicar e Manter atual. Parseia TP/STOP de valor_novo via regex.
file: atlas_ui/src/components/GestaoView/TuneApprovalCard.jsx
role: UI de aprovação — permite ao CEO aceitar ou rejeitar parâmetros TUNE sugeridos.
input:
  - ticker: str — código do ativo
  - onAplicar: function(ticker, tpSugerido, stopSugerido) — callback de aplicação
output:
  - Render: card com TP/STOP atual vs sugerido + botões de ação
depends_on:
  - [[SYSTEMS/atlas/modules/GestaoView]]
depends_on_condition: []
used_by:
  - [[SYSTEMS/atlas/modules/GestaoView]]
intent:
  - Superficiar resultado TUNE de forma acionável — o CEO decide se aplica ou mantém os parâmetros atuais.
constraints:
  - API_BASE = http://localhost:8000 (hardcoded)
  - Regex de parse: /TP=([\d.]+)\s+STOP=([\d.]+)/ em valor_novo
  - Fetch de /ativos/{ticker} para obter dados do TUNE
  - Botão Aplicar chama onAplicar(ticker, tpSugerido, stopSugerido)
  - Botão Manter atual descarta o card
notes:
  - 2026-04-26: código modificado — TuneApprovalCard.jsx
  - API_BASE hardcoded — migrar para env config quando disponível
