---
uid: mod-atlas-011
version: 1.0.2
status: validated
owner: Chan

function: Componente React de visualização detalhada de ativo individual. Exibe resumo executivo (regime, EDGE state, IR, sizing), gráficos (walk-forward, distribuição, ACF, fat-tails), histórico de ciclos ORBIT, histórico REFLECT, histórico de configurações e posições abertas.
file: atlas_ui/src/components/AtivoView.jsx
role: View de detalhe de ativo — dashboard completo por ticker para análise e decisão.

input:
  - ticker: str — ativo selecionado via rota ou prop
  - dados via fetch da API /delta-chaos/ativos/{ticker}

output:
  - DOM: dashboard com múltiplas seções colapsáveis (resumo, gráficos, histórico, config)

depends_on:
  - [[SYSTEMS/atlas/modules/API_ROUTES]]
  - [[SYSTEMS/atlas/modules/regimeColors]]
  - [[SYSTEMS/atlas/modules/systemStore]]

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/UI_CORE]]

intent:
  - Prover visão completa de um ativo para que o CEO avalie regime, edge state, parâmetros e posição antes de tomar decisão.

constraints:
  - Importa getRegimeColor e getRegimeBgColor de ../store/regimeColors
  - Gráficos via componentes: WalkForwardChart, DistributionChart, ACFChart, TailMetrics
  - Dados carregados via fetch com useEffect + loading state
  - Componente monolítico (~62KB) — candidato a refatoração futura

notes:
  - 2026-04-13: código modificado — AtivoView.jsx
---