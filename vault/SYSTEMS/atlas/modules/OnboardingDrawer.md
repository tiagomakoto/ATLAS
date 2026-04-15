---
uid: mod-atlas-018
version: 1.0.3
status: validated
owner: Chan

function: Drawer lateral para onboarding de novo ativo. Coleta ticker e configurações iniciais, dispara POST /delta-chaos/calibracao/iniciar e acompanha progresso dos 3 steps (backtest_dados, tune, backtest_gate).
file: atlas_ui/src/components/GestaoView/OnboardingDrawer.jsx
role: Formulário de onboarding — interface para adicionar novos ativos ao sistema.

input:
  - Interações do CEO: ticker, parâmetros iniciais
  - Status de calibração via polling GET /delta-chaos/calibracao/{ticker}

output:
  - DOM: drawer com formulário, stepper de progresso (3 steps) e log de execução

depends_on:
  - [[SYSTEMS/atlas/modules/API_ROUTES]]

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/GestaoView]]

intent:
  - Guiar o CEO pelo fluxo de onboarding com feedback visual em tempo real.

constraints:
  - 3 steps sequenciais: backtest_dados → tune → backtest_gate
  - Polling de status a cada intervalo para atualização do stepper
  - Validação de ticker: regex ^[A-Z0-9]{4,6}$

notes:
  - 2026-04-14: código modificado — OnboardingDrawer.jsx
  - 2026-04-13: código modificado — OnboardingDrawer.jsx
---