# System Overview

## Sistemas ativos
- ATLAS: dashboard supervisório (FastAPI backend + React frontend)
- Delta Chaos: sistema quantitativo de venda de volatilidade no mercado brasileiro (B3)
- Advantage: sistema de decisao para trading em B3. Arquitetura em 4 camadas: DATA LAYER → CAUSA (C1) → EXPRESSAO (C2) → EXTRACAO (C3). Data Layer operacional com 4 dominios SQLite e 5 coletores. Fase atual: Data Layer.

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

## Vault — operação via MCP filesystem
- Vault local: C:\Users\tiago\OneDrive\Documentos\ATLAS\vault\
- Todos os agentes rodam no Claude Desktop — MCP filesystem disponível em todos os Projetos
- Agentes escrevem diretamente no vault via MCP — não produzem texto para o CEO colar
- CEO intervém apenas para: aprovar fechamento de tensão, confirmar BOARD_REVIEW_REQUIRED
- Caminhos canônicos:
  - Atas: BOARD/atas/YYYY-MM-DD_<tema>.md
  - Tensões abertas: BOARD/tensoes_abertas/<uid>_<slug>.md
  - Decisões fechadas: BOARD/decisoes/<uid>_<slug>.md
  - Índice vivo: BOARD/decision_log.md
  - Templates: TEMPLATES/tensao_template.md | ata_template.md