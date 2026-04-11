---
uid: mod-advantage-010
version: 1.0
status: validated
owner: Chan

function: Prover utilitários cross-domain para validação e instrumentação de requisições do Data Layer.
file: advantage/src/data_layer/utils.py
role: Biblioteca utilitária passiva (helpers)

input:
  - Any (DataFrames, dados formativos, decoradores)

output:
  - DataFrames validados, logs no stdout.

depends_on:

depends_on_condition:

used_by:
  - [[SYSTEMS/advantage/modules/COLLECTORS]]
  - [[SYSTEMS/advantage/modules/SCHEDULER]]

intent:
  - Centralizar a lógica trivial que seria duplicada pelo código (retry loops defensivos, validação de flags) permitindo manter os crawlers limpos e centrados em payload json.

constraints:
  - `validar_ohlcv` exige abertura, maxima, minima, fechamento e volume. Inconsistências (abertura>maxima, volume<0) injetam `flag_qualidade=0` mas NUNCA descartam a row.
  - retry com backoff sleep. Defaut: 3 tentativas, 5s delay.
  - Os logs seguem estrita anatomia `[TIMESTAMP] [FONTE] registros=N status=...`

notes:
---
