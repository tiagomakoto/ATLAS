---
uid: mod-atlas-001
version: 1.0.12
status: validated
owner: Chan

function: Executa subprocessos do Delta Chaos (modos atômicos e diários) de forma assíncrona, parseia output e emite eventos estruturados sem bloquear o API loop. Também orquestra o ciclo completo dc_daily e o fluxo de calibração (onboarding) de novos ativos.
file: atlas_backend/core/dc_runner.py
role: Orquestrador e fronteira de execução (único ponto de integração de processos entre ATLAS e Delta Chaos).

input:
  - tickers: list — lista de códigos dos ativos para processamento
  - action_payload: dict — payload da requisição para emissão no bus
  - modo: str — nome do modo do edge.py (eod, orbit_update, etc.)

output:
  - dict: {"status": "OK"|"ERRO", "returncode": int, "output": str} (além disso, eventos no event_bus)
  - run_digest: dict — resumo de execução retornado por dc_daily (gate_eod, xlsx lido, TP/STOP acionado)

depends_on:
  - [[SYSTEMS/delta_chaos/modules/EDGE]]
  - [[SYSTEMS/atlas/modules/EVENT_BUS]]
  - [[SYSTEMS/atlas/modules/DATA_READERS]]

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/API_ROUTES]]

intent:
  - Isolar a execução do Delta Chaos como subprocessos desacoplados, mantendo robustez contra crashes e assegurando feedback em tempo real para o front (logs e progresso) através de JSONL parsers.

constraints:
  - Retorno de _sync_runner tem timeout de 1800s.
  - Váriaveis de ambiente PYTHONPATH, PYTHONIOENCODING e PYTHONUTF8 são setadas explicitamente para o subprocess.
  - _watch_events lê f"events_{run_id}.jsonl" do TMP_DIR de forma contínua em thread separada.
  - Evento de "dc_module_complete" em "GATE" com status "error" é emitido se o ativo não tiver historico_config (onboarding incompleto).
  - dc_daily orquestra: verificar dados → reflect_daily → TP/STOP → gate_eod → bloco mensal (orbit_update) se ciclo mudou.
  - dc_calibracao_iniciar cria campo calibracao no master JSON e dispara step 1 em background via asyncio.create_task.
  - _executar_calibracao_step1 encadeia automaticamente: backtest_dados → tune → backtest_gate.
  - Polling SQLite para progresso TUNE: thread lê tune_{TICKER}.db em modo read-only a cada 200ms e emite dc_tune_progress.
  - _dc_running controla concorrência global no namespace.
  - dc_calibracao_retomar verifica status == "paused" antes de retomar step.
  - dc_calibracao_progresso_tune usa conexão SQLite read-only explícita (file:?mode=ro).
  - _tune_elegivel verifica >= 126 dias úteis desde último TUNE.
  - _ciclo_mudou compara mês do OHLCV cache com último ciclo do historico.
  - _verificar_tp_stop lê preço do xlsx e calcula pnl vs take_profit/stop_loss.
  - _atualizar_ativo_store emite daily_ativo_updated para manter frontend sincronizado.

notes:
  - 2026-04-15: código modificado — dc_runner.py
  - 2026-04-15: código modificado — dc_runner.py
  - 2026-04-15: código modificado — dc_runner.py
  - 2026-04-15: código modificado — dc_runner.py
  - 2026-04-15: código modificado — dc_runner.py
  - 2026-04-15: código modificado — dc_runner.py
  - 2026-04-15: código modificado — dc_runner.py
  - 2026-04-14: código modificado — dc_runner.py
  - 2026-04-14: código modificado — dc_runner.py
  - 2026-04-14: código modificado — dc_runner.py
  - 2026-04-13: código modificado — dc_runner.py
  - _dc_running é usado para bloqueio/concorrência global no namespace.
  - dc_daily orquestra nativamente o fallback de meses (orbit update) se o ciclo virar.
  - Funções públicas: dc_eod, dc_orbit_backtest, dc_tune, dc_gate_backtest, dc_orbit_update, dc_reflect_daily, dc_gate_eod, dc_reflect_cycle, dc_daily, dc_calibracao_iniciar, dc_calibracao_retomar, dc_calibracao_progresso_tune
---
