# Estado atual do projeto ATLAS

## Implementado
- ✅ Encoding fix (9 arquivos delta_chaos)
- ✅ SPEC v2.6 — Backend (orquestrador + patch gate.py)
- ✅ SPEC v2.6 — Frontend (digest por ativo + StatusTransitionCard)
- ✅ DEBUG_TICKER flag
- ✅ Reset de ciclos para debug
- ✅ LogDrawer + botão Check Status corrigidos

## Pendente no SPEC v2.6
- ❌ gate.py — registro de falha em historico_config[] (patch antes de raise ValueError)
- ❌ Novos modos CLI em edge.py (orbit, reflect_daily, gate_eod, backtest_dados, backtest_gate)
- ❌ Novas funções em dc_runner.py (run_orbit_update, run_reflect_daily, run_gate_eod)

## Bugs conhecidos
- ⚠️ event_bus.py não funciona em threads separadas (eventos não chegam via WebSocket)

## Como rodar
```bash
python run_server.py  # reset + uvicorn
```

## Paths
- Backend: `atlas_backend/`
- Frontend: `atlas_ui/src/`
- Delta Chaos: `delta_chaos/`
- Ativos: `G:\Meu Drive\Delta Chaos\ativos\`
- OHLCV: `G:\Meu Drive\Delta Chaos\TAPE\ohlcv\`
