---
uid: mod-atlas-017
version: 1.0.7
status: validated
owner: Chan

function: View de gestão de ativos com abas para onboarding de novos ativos e calibração. Integra OnboardingDrawer e CalibracaoDrawer como sub-componentes modais/drawer.
file: atlas_ui/src/components/GestaoView.jsx
role: Tela de gestão — administração do ciclo de vida dos ativos (onboarding, calibração, parâmetros).

input:
  - Interações do CEO (botões de ação, seleção de ativo)
  - Dados da API via fetch

output:
  - DOM: view com abas e drawers laterais para gestão

depends_on:
  - [[SYSTEMS/atlas/modules/API_ROUTES]]
  - [[SYSTEMS/atlas/modules/systemStore]]

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/UI_CORE]]

intent:
  - Centralizar todas as ações de gestão de ativos em uma única tela organizada por abas.

constraints:
  - Integra CalibracaoDrawer e OnboardingDrawer como sub-componentes
  - Ações passam por confirmação (confirm=true + description obrigatória)

notes:
  - 2026-04-22: código modificado — GestaoView.jsx
  - 2026-04-22: código modificado — GestaoView.jsx
  - 2026-04-17: código modificado — GestaoView.jsx
  - 2026-04-17: código modificado — GestaoView.jsx
  - 2026-04-14: código modificado — GestaoView.jsx
  - 2026-04-14: código modificado — GestaoView.jsx
---