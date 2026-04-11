---
uid: mod-advantage-009
version: 1.0.4
status: validated
owner: Chan

function: Orquestrador em background (APScheduler) para executar o schedule de todos os coletores de dados e computar subprodutos (indicadores).
file: advantage/src/data_layer/scheduler.py
role: Cron daemon de ingestão e pré-processamento persistente.

input:
  - Coletores a rodar em CronTriggers ou IntervalTriggers (ex: hora, mi, weekday).

output:
  - Número de registros inseridos.
  - Indicadores SMA, EMA, MACD, RSI, etc calculados tabelados (`indicadores_compartilhados`).

depends_on:
  - [[SYSTEMS/advantage/modules/DATA_LAYER]]
  - [[SYSTEMS/advantage/modules/COLLECTORS]]

depends_on_condition:

used_by:

intent:
  - Isolar a responsabilidade de timing e execuções cadenciadas do loop do event bus central ou das chamadas de interface do usuário, rodando de forma estritamente headless (`BlockingScheduler`).

constraints:
  - Preço e Volume: 18:30h UTC-3
  - Macro BR: 19:00 UTC-3
  - Macro GL: 19:30 UTC-3
  - Alternativo: Segundas 08:00 UTC-3
  - Noticias: Intervalos de 30min
  - Indicadores: 20:00 UTC-3
  - `calcular_indicadores` só puxa ativos em lote limit e com `flag_qualidade = 1`. Mínimo 20 bars.

notes:
  - 2026-04-11: código modificado — scheduler.py
  - 2026-04-10: código modificado — scheduler.py
  - 2026-04-10: código modificado — scheduler.py
  - 2026-04-10: código modificado — scheduler.py
  - O cálculo de indicadores usa pandas-ta.
---