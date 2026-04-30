---
uid: mod-delta-001
version: 1.2.7
status: validated
owner: Chan

function: Responsável único por acesso a dados externos — OHLCV, IBOV, séries externas, gregas, SELIC, master JSON. Único ponto de contato com fontes externas no sistema.
file: delta_chaos/tape.py
role: Camada de dados — nenhum outro módulo acessa dados externos diretamente

input:
  - ticker: str — código do ativo
  - data_ref: date — data de referência para leitura
  - cfg_ativo: dict — configuração do ativo carregada do master JSON

output:
  - master_json: dict — estado completo do ativo (OHLCV, gregas, séries externas, REFLECT)
  - cotahist: DataFrame — histórico de opções por ativo e data
  - sizing_reflect: float — multiplicador de sizing do REFLECT para o EDGE

depends_on:

depends_on_condition:

used_by:
  - [[SYSTEMS/delta_chaos/modules/EDGE]]
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]

intent:
  - Isolar completamente o acesso a dados externos. Nenhum módulo downstream conhece fontes — só o TAPE.

constraints:
  - tape_salvar_ativo() usa os.replace() — escrita atômica obrigatória
  - _cache_ok() nunca retorna True para arquivo inexistente — os.path.exists verificado antes de os.path.getsize
  - _baixar_cotahist retorna lista — anual=[1 item], mensais=[N itens], vazio=[]
  - Threshold dinâmico por ano para COTAHIST e gregas — anos antigos têm threshold menor
  - Strikes do arquivo EOD divididos por 100 para chegar ao preço real
  - COTAHISTs em TAPE_DIR/cotahist/ — subpasta confirmada
  - tape_paper() valida freshness do xlsx — threshold 16h
  - open_interest incluído no _ler_cotahist — necessário para GEX e REFLECT
  - Volume usa campo Lanc. como proxy quando Vol. Financeiro ausente

notes:
  - 2026-04-30: código modificado — tape.py
  - 2026-04-30: código modificado — tape.py
  - 2026-04-30: código modificado — tape.py
  - 2026-04-29: código modificado — tape.py
  - 2026-04-29: código modificado — tape.py
  - 2026-04-16: código modificado — tape.py
  - 2026-04-14: código modificado — tape.py
  - tape_reflect_daily — calcula componentes EOD, armazena no daily_history
  - tape_reflect_cycle — calcula estado REFLECT mensal, emite estado A-E
  - tape_sizing_reflect() ativa a partir do EDGE v1.3
  - tape_paper() header=1 — pula titulo linha 0, normaliza colunas com remocao de caracteres especiais
  - Strike e fechamento divididos por 100 quando mediana > threshold
  - Q10 aberto: S6 VALE3 congelado 2024-Q1 — investigar falha yfinance
---
