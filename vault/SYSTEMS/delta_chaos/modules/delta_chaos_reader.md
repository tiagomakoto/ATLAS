---
uid: mod-delta-009
version: 1.0.7
status: validated
owner: Chan

function: Interface de leitura e escrita do master JSON dos ativos produzido pelo Delta Chaos. Sanitiza NaN, calcula status derivado (OPERAR, MONITORAR, SEM_EDGE, SUSPENSO), enriquece com staleness_days e calibracao.
file: atlas_backend/core/delta_chaos_reader.py
role: Leitor/escritor de estado do ativo — traduz JSON cru para estrutura consumível pelo backend.

input:
  - ticker: str — identificador do ativo
  - updates: dict — campos a atualizar (para update_ativo)
  - fonte: str — "backtest" | "paper" | "live" (para get_book)

output:
  - dict: JSON enriquecido com status, staleness_days, calibracao, reflect_historico, core, historico
  - list: lista de tickers encontrados em config_dir (para list_ativos)

depends_on:

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/ATLAS_DC_RUNNER]]
  - [[SYSTEMS/atlas/modules/API_ROUTES]]

intent:
  - Abstrair acesso ao master JSON do ativo para todo o ecossistema ATLAS.
  - NOTA: este módulo é coberto semanticamente por [[SYSTEMS/atlas/modules/DATA_READERS]] — mantido separado por granularidade de arquivo.

constraints:
  - sanitize_nan converte float NaN para None — evita corrupção JSON
  - get_ativo retorna historico_config como booleano (true se len > 0)
  - Status derivado: quedas REFLECT >=2 → SUSPENSO | último GATE OPERAR + IR>0 + REFLECT A/B → OPERAR
  - reflect_historico filtra por ciclos existentes no historico ORBIT — órfãos descartados
  - get_ativo retorna calibracao com estrutura padrão (3 steps) quando ausente
  - update_ativo incrementa version, injeta history em ticker_history.json
  - get_book valida fonte antes de ler — aceita backtest, paper, live

notes:
  - 2026-04-26: código modificado — delta_chaos_reader.py
  - 2026-04-17: código modificado — delta_chaos_reader.py
  - 2026-04-17: código modificado — delta_chaos_reader.py
  - 2026-04-16: código modificado — delta_chaos_reader.py
  - 2026-04-14: código modificado — delta_chaos_reader.py
  - 2026-04-13: código modificado — delta_chaos_reader.py
  - Funções públicas: list_ativos, get_ativo, update_ativo, get_book, sanitize_nan, sanitize_record
---