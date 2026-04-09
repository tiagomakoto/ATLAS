# System Overview

## Sistemas ativos
- ATLAS: dashboard supervisório (FastAPI backend + React frontend)
- Delta Chaos: sistema quantitativo de venda de volatilidade no mercado brasileiro (B3)
- Advantage: em estágio embrionário — DATA LAYER com 18 fontes prevista

## Relação entre sistemas
- ATLAS é o frontend supervisório para subprocessos
- Delta Chaos roda como subprocess do ATLAS via dc_runner.py (módulo de fronteira)
- Advantage será acoplado ao ATLAS futuramente

## Board
- Board Delta Chaos: 9 agentes especializados
- Board Advantage: composição diferente, mesma dinâmica
- Agentes transversais: Howard Marks, Taleb, Derman, Thorp
- Decisões do board registradas em BOARD/atas/ e BOARD/decision_log.md

## Planner/Executor
- OpenCode (agentes Plan/Build/Debugger) tem acesso ao código completo
- SCM serve ao board — não substitui leitura de código pelo planner
- Planner usa vault como mapa arquitetural, não como fonte de implementação