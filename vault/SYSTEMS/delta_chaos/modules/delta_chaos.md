---
uid: mod-delta-010
version: 1.0.5
status: validated
owner: Chan

function: Router FastAPI com endpoints HTTP para todas as operações do Delta Chaos — EOD, ORBIT, TUNE, GATE, calibração completa (onboarding), daily run, aplicação de parâmetros TUNE. Cada endpoint valida confirm+description antes de executar.
file: atlas_backend/api/routes/delta_chaos.py
role: Interface HTTP do Delta Chaos — expõe todos os modos de execução como endpoints REST.

input:
  - Requests HTTP (POST) com payloads JSON (EodPayload, TickerPayload, CalibracaoPayload)

output:
  - Respostas JSON: {status, output, relatorio?} — resultado do subprocesso executado

depends_on:
  - [[SYSTEMS/atlas/modules/ATLAS_DC_RUNNER]]
  - [[SYSTEMS/atlas/modules/DATA_READERS]]
  - [[SYSTEMS/atlas/modules/relatorios]]

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/UI_CORE]]

intent:
  - Expor cada modo do Delta Chaos como endpoint HTTP, com validação de confirmação obrigatória.
  - NOTA: este módulo é coberto semanticamente por [[SYSTEMS/atlas/modules/API_ROUTES]] — mantido separado por granularidade de arquivo.

constraints:
  - _validar_confirm exige confirm=true e description não vazia antes de executar qualquer ação
  - _validar_ticker verifica existência do ticker em list_ativos()
  - _resolver_xlsx_dir usa fallback para delta_chaos_base/opcoes_hoje se xlsx_dir não informado
  - POST /tune gera relatório automaticamente após TUNE bem-sucedido — extrai TP/STOP sugeridos via regex
  - POST /tune/aplicar: escrita atômica com os.replace, registra em historico_config, marca relatório como aplicado
  - POST /calibracao/iniciar: dispara dc_calibracao_iniciar em background
  - GET /calibracao/{ticker}: reconciliação watchdog — se running + ultimo_evento_em > 10min → paused
  - POST /calibracao/{ticker}/retomar: retoma step pausado
  - GET /calibracao/{ticker}/progresso-tune: lê tune_TICKER.db via conexão read-only
  - POST /daily/run: executa dc_daily para todos os ativos parametrizados
  - Validação de ticker: regex ^[A-Z0-9]{4,6}$

notes:
  - 2026-04-17: código modificado — delta_chaos.py
  - 2026-04-15: código modificado — delta_chaos.py
  - 2026-04-14: código modificado — delta_chaos.py
  - 2026-04-13: código modificado — delta_chaos.py
  - Endpoints: /eod/executar, /orbit, /tune, /gate, /calibracao, /daily/run, /tune/aplicar, /calibracao/iniciar, /calibracao/{ticker}, /calibracao/{ticker}/retomar, /calibracao/{ticker}/progresso-tune
---