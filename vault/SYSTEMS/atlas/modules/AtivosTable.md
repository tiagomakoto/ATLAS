---
uid: mod-atlas-016
version: 1.0.1
status: validated
owner: Chan

function: Tabela de ativos parametrizados com status, regime, REFLECT state, sizing, IR e staleness. Dados alimentados via systemStore (ativosParametrizados) preenchido por eventos daily_ativo_updated.
file: atlas_ui/src/components/AtivosTable.jsx
role: Tabela de overview — visão consolidada de todos os ativos para triagem rápida pelo CEO.

input:
  - ativosParametrizados: array — lista de ativos com dados enriquecidos do systemStore

output:
  - DOM: tabela HTML com colunas por métricas críticas

depends_on:
  - [[SYSTEMS/atlas/modules/systemStore]]
  - [[SYSTEMS/atlas/modules/regimeColors]]

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/UI_CORE]]

intent:
  - Exibir overview rápido do estado de todos os ativos em uma única tabela escaneável.

constraints:
  - Dados vêm do systemStore — não faz fetch direto
  - Cores de regime via regimeColors

notes:
  - 2026-04-13 — módulo criado automaticamente a partir de atlas_ui/src/components/AtivosTable.jsx
---