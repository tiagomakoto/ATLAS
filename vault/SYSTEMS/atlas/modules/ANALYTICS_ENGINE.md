---
uid: mod-atlas-008
version: 1.0
status: validated
owner: Chan

function: Central agregadora de métricas de session, PnL e histórico em stream para reportes e analytics tabulados.
file: atlas_backend/core/analytics_engine.py, atlas_backend/core/analytics_stream.py, atlas_backend/core/session_report.py
role: Analytics — formador das visualizações estatísticas da camada de negócios.

input:
  - JSON dados de book via reader
  
output:
  - dict com agregados matematicos dos regimes, pnl total, pnl por edge

depends_on:
  - [[SYSTEMS/atlas/modules/DATA_READERS]]

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/API_ROUTES]]

intent:
  - Separar calculos massivos de Pnl e reports do backend síncrono para abstraçoes autônomas analiticas, gerando agregados rapidamente pras rotas sem impactar health da master app.

constraints:

notes:
---
