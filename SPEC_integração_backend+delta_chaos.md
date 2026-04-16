CONTEXTO
Sistema: ATLAS — backend FastAPI + Delta Chaos (Python)
Camada: Integração backend — atlas_backend/core/dc_runner.py + delta_chaos/edge.py
Tecnologia relevante: Python, asyncio, threading, FastAPI/uvicorn


SITUAÇÃO ATUAL

dc_runner.py atua como orquestrador ATLAS↔Delta Chaos. Para cada modo
de execução (backtest_dados, tune, backtest_gate, orbit_update,
reflect_daily, gate_eod), dc_runner.py chama _stream_subprocess(), que:
  1. Abre edge.py como processo filho via subprocess.Popen
  2. Passa --modo <nome> como argumento CLI
  3. Lê stdout do processo filho linha a linha
  4. Emite eventos WebSocket (emit_dc_event) a partir do processo pai

edge.py é atualmente um script CLI executado como processo filho. Ele:
  1. Recebe --modo via argparse (ou equivalente)
  2. Executa a lógica de negócio do Delta Chaos
  3. Escreve eventos em arquivo JSONL (tmp/events_{run_id}.jsonl)
  4. O dc_runner lê esse JSONL em thread paralela (_watch_events_inner)
     e converte em eventos WebSocket

A comunicação entre os dois processos usa três canais simultâneos:
  - stdout (logs em texto)
  - arquivo JSONL temporário (eventos estruturados)
  - variável de ambiente ATLAS_RUN_ID (isolamento de run)

Arquivos relevantes:
  - atlas_backend/core/dc_runner.py  (orquestrador/runner)
  - delta_chaos/edge.py              (lógica de negócio)


COMPORTAMENTO DESEJADO

Eliminar o modelo subprocess. dc_runner.py deve importar edge.py como
módulo Python e chamar suas funções diretamente, no mesmo processo.

Resultado esperado após a mudança:

1. dc_runner.py importa delta_chaos.edge e chama funções por modo:
   - "backtest_dados" → edge.rodar_backtest_dados(ticker, anos)
   - "tune"           → edge.rodar_tune(ticker)
   - "backtest_gate"  → edge.rodar_backtest_gate(ticker)
   - "orbit_update"   → edge.rodar_orbit_update(ticker, anos)
   - "reflect_daily"  → edge.rodar_reflect_daily(ticker, xlsx_path)
   - "gate_eod"       → edge.rodar_gate_eod(ticker)
   Os nomes exatos das funções podem ser propostos pela equipe de código
   com base no que já existe em edge.py — o contrato é: uma função
   pública por modo, com parâmetros explícitos.

2. edge.py expõe essas funções como módulo importável. O bloco
   if __name__ == "__main__": pode ser mantido para uso manual futuro,
   mas não é o caminho principal de execução.

3. emit_event (JSONL) em edge.py deixa de ser necessário como canal
   de comunicação. edge.py pode chamar emit_dc_event diretamente do
   atlas_backend (já que agora roda no mesmo processo/loop do uvicorn).
   ATENÇÃO: emit_dc_event usa call_soon_threadsafe — edge.py continuará
   sendo chamado a partir de threads (asyncio.to_thread). Esse padrão
   deve ser preservado.

4. Toda chamada a função de edge.* dentro do dc_runner deve estar
   envolvida em try/except com:
   - captura da exceção tipada
   - emit de erro estruturado via emit_dc_event (status="error")
   - emit_log com nível "error"
   - não relançar a exceção para o uvicorn (isolar falha por estágio)

5. _stream_subprocess(), _watch_events_inner(), _flush_events(),
   _watch_events(), _get_dc_script() e a lógica de arquivo JSONL
   temporário em dc_runner.py são removidos após a migração.

6. As variáveis de ambiente ATLAS_RUN_ID, PYTHONUNBUFFERED e
   PYTHONIOENCODING deixam de ser necessárias para este fluxo e devem
   ser removidas do dc_runner.

7. emit_log e emit_error em edge.py (hoje definidos como wrappers de
   print) devem ser substituídos por importação direta de
   atlas_backend.core.terminal_stream — já que o módulo agora roda
   no mesmo processo.

8. O polling de SQLite para progresso do TUNE (_poll_sqlite em
   dc_runner.py) deve ser preservado — ele roda em thread separada e
   não depende do modelo subprocess. Apenas remover a lógica de
   subprocess ao redor dele.

9. dc_calibracao_iniciar() e _executar_calibracao_step1() em
   dc_runner.py já chamam dc_orbit_backtest(), dc_tune(),
   dc_gate_backtest() internamente — após a migração, essas funções
   chamarão as funções de edge.py diretamente. A estrutura de
   sequenciamento (step 1 → 2 → 3) não muda.


NÃO TOCAR

- Lógica de negócio dentro de edge.py (ORBIT, TUNE, GATE, REFLECT,
  FIRE, BOOK) — apenas expor como funções públicas, sem alterar
  o que cada modo faz internamente
- Estrutura de eventos WebSocket: dc_module_start, dc_module_complete,
  dc_tune_progress, daily_ativo_updated, daily_ativo_complete —
  tipos, payloads e ordem de emissão devem ser preservados
- dc_daily() — fluxo de orquestração diária não muda; apenas as
  chamadas internas (dc_orbit_update, dc_gate_eod, etc.) passam a
  usar funções diretas em vez de subprocess
- Polling SQLite para TUNE (_poll_sqlite) — manter intacto
- Lógica de calibração (dc_calibracao_iniciar, _executar_calibracao_step1,
  dc_calibracao_retomar, dc_calibracao_progresso_tune) — estrutura
  preservada, apenas substituir chamadas de subprocess por chamadas
  diretas
- atlas_backend/core/event_bus.py — não modificar
- Qualquer arquivo fora de dc_runner.py e delta_chaos/edge.py

A equipe deve sinalizar ao CEO qualquer impacto colateral identificado
antes de executar — especialmente em módulos que importam dc_runner.py.


ADENDO 1 — Substituição de emit_event em edge.py:
Cada chamada emit_event(modulo, "start") deve ser substituída por:
  emit_dc_event("dc_module_start", modulo, "running", ticker=ticker)
Cada chamada emit_event(modulo, "done") deve ser substituída por:
  emit_dc_event("dc_module_complete", modulo, "ok", ticker=ticker)
Cada chamada emit_event(modulo, "error") deve ser substituída por:
  emit_dc_event("dc_module_complete", modulo, "error", ticker=ticker)
Não remover chamadas de sinalização sem substituir. Silêncio no
drawer é bug silencioso — o pior tipo.

ADENDO 2 — Bloco __main__ em edge.py:
O bloco if __name__ == "__main__": deve ser mantido. Não remover.

ADENDO 3 — Funções de edge.py são bloqueantes:
Todas as funções públicas de edge.py executam I/O pesado (pandas,
Optuna, leitura de parquet/JSON). Elas NÃO são corrotinas async.
Cada chamada dentro dos wrappers async do dc_runner (dc_tune,
dc_orbit_backtest, dc_gate_backtest, etc.) deve usar:
  await asyncio.to_thread(edge.rodar_X, arg1, arg2, ...)
Nunca chamar edge.rodar_X() diretamente dentro de função async
sem asyncio.to_thread — isso trava o uvicorn.