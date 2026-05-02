---
uid: mod-atlas-012
version: 1.0.3
status: validated
owner: Chan

function: Painel de resumo por ativo do ciclo de manutenção diário. Exibe xlsx eod, posição, tp/stop, bloco mensal (regime, reflect, status) com transições coloridas antes→depois.
file: atlas_ui/src/components/DigestPanel.jsx
role: Dashboard de digest — visualização consolidada do resultado do dc_daily por ativo.

input:
  - digestPorAtivo: dict — objeto {ticker: digest} vindo do systemStore
  - timestamp: str — timestamp ISO do digest

output:
  - DOM: painel monospace com ícones (✓/✗/~) e cores por status de cada campo do digest

depends_on:
  - [[SYSTEMS/atlas/modules/systemStore]]
  - [[SYSTEMS/atlas/modules/regimeColors]]

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/UI_CORE]]

intent:
  - Exibir resultado do ciclo de manutenção em formato terminal estilizado para leitura rápida pelo CEO.

constraints:
  - Importa getRegimeColor de ../store/regimeColors — fonte única de cores de regime
  - Campos renderizados por ativo: xlsx eod, posição, tp/stop, bloco mensal (regime, reflect, status)
  - Bloco mensal renderiza transição ORBIT antes→depois com cores individuais por regime
  - Bloco mensal renderiza transição REFLECT antes→depois com cores por estado (A=verde, B=azul, C=âmbar, D/E=vermelho)
  - Bloco mensal renderiza transição STATUS antes→depois com cores (OPERAR=verde, MONITORAR=âmbar)
  - Ativos bloqueados exibem motivo em vermelho + gate_eod = BLOQUEADO
  - TP/STOP exibe status: ok (mantendo), fechar (motivo), sem_xlsx

notes:
  - 2026-05-02: código modificado — DigestPanel.jsx
  - 2026-04-14: código modificado — DigestPanel.jsx
  - Componente puramente funcional — sem estado interno, renderiza props
---