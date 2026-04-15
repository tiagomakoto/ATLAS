---
uid: mod-atlas-003
version: 1.0.1
status: validated
owner: Chan

function: Interface central para leitura agregada e semântica do master JSON (config dos ativos) e do book JSON produzidos pelo Delta Chaos.
file: atlas_backend/core/delta_chaos_reader.py, atlas_backend/core/book_manager.py
role: Leitos de estado — abstrai a estrutura crua do JSON gerado do Delta Chaos e provê lógica de status e extração de dados mastigados.

input:
  - ticker: str — identificador do ativo para query no arquivo de config.
  - updates: dict — objeto contendo modificações no JSON para salvamento.

output:
  - dict: JSON completo do ativo em `get_ativo`, enriquecido com `status`, `staleness_days`, `calibracao` e arrays extraídos/sanitizados.
  - dict: Posicões e PnL retornados por `get_book`.

depends_on:

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/ATLAS_DC_RUNNER]]
  - [[SYSTEMS/atlas/modules/API_ROUTES]]
  - [[SYSTEMS/atlas/modules/ANALYTICS_ENGINE]]

intent:
  - Abstrair o modelo de dados de arquivo físico (.json) para o restante da aplicação ATLAS, permitindo injeção de lógica condicional de estado (ex: "STATUS", "STALENESS") por cima do dado gerado assincronamente.

constraints:
  - `sanitize_nan` converte `NaN` Python para `None` no output, evitando corrupção ou quebra do parser JSON.
  - `update_ativo` sempre atualiza version (+1) e injeta history (`ticker_history.json`) de forma atômica para cada atualização de config.
  - O Status deriva implicitamente de regressão no `reflect_history[...state]` e `historico_config`, não é um campo persistido no estado bruto.
  - get_ativo retorna campo `calibracao` com estrutura padrão (step_atual, steps 1-3, ultimo_evento_em) quando ausente no master JSON.
  - get_ativo retorna `historico_config` como booleano (true se tem registros) — não o array completo.
  - get_book aceita fonte "backtest" | "paper" | "live" — valida antes de abrir arquivo.
  - reflect_historico filtrado por ciclos existentes no historico ORBIT — ciclos órfãos descartados.
  - Quedas consecutivas REFLECT (D ou E) >= 2 resultam em status SUSPENSO.

notes:
  - Se faltar historico, último ciclo setar `lock`, estado será SUSPENSO. Duas quedas no reflector também suspendem a engine para o ativo.
  - Funções públicas: list_ativos, get_ativo, update_ativo, get_book, sanitize_nan, sanitize_record
---
