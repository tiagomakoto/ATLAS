---
uid: mod-atlas-020
version: 1.0.2
status: validated
owner: Chan

function: Tab de relatórios TUNE no frontend. Lista relatórios do index.json, exibe detalhes expandidos com parâmetros sugeridos vs atuais, e permite aplicar parâmetros aprovados pelo CEO via POST /delta-chaos/tune/aplicar.
file: atlas_ui/src/components/RelatorioTab.jsx
role: Interface de relatórios — visualização e ação sobre relatórios de TUNE e ONBOARDING.

input:
  - Dados via fetch GET /delta-chaos/relatorios
  - Interações do CEO: expandir, aplicar, rejeitar

output:
  - DOM: lista expandível de relatórios com botões de ação

depends_on:
  - [[SYSTEMS/atlas/modules/API_ROUTES]]

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/UI_CORE]]

intent:
  - Prover interface para que o CEO avalie e aplique ou rejeite parâmetros sugeridos pelo TUNE.

constraints:
  - Aplicação dispara POST com confirm=true e description obrigatória
  - Relatórios aplicados ficam marcados como "aplicado" no index.json

notes:
  - 2026-04-26: código modificado — RelatorioTab.jsx
  - 2026-04-13 — módulo criado automaticamente a partir de atlas_ui/src/components/RelatorioTab.jsx
---