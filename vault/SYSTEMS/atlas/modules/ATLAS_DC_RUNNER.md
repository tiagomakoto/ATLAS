---
uid: mod-atlas-001
version: 1.0.2
status: validated
owner: Chan

function: Executa subprocessos do Delta Chaos (modos atômicos e diários) de forma assíncrona, parseia output e emite eventos estruturados sem bloquear o API loop.
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

notes:
  - 2026-04-14: código modificado — dc_runner.py
  - 2026-04-13: código modificado — dc_runner.py
  - _dc_running é usado para bloqueio/concorrência global no namespace.
  - dc_daily orquestra nativamente o fallback de meses (orbit update) se o ciclo virar.
---
