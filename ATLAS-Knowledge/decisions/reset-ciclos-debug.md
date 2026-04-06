# Reset de ciclos para debug do orquestrador

## Contexto
O orquestrador detecta ciclo novo comparando `ohlcv_month > ultimo_ciclo`. Se ambos são `2026-04`, o bloco mensal é pulado.

## Problema
Para testar o bloco mensal, precisaríamos esperar até maio/26.

## Decisão
No `run_server.py`, `reset_historico_ativos()` roda **sempre** ao iniciar o servidor. Remove ciclos de `2025-03` até `2026-04`, deixando o último ciclo em `2025-02`.

## Resultado
`ohlcv_month` ("2026-04") > `ultimo_ciclo` ("2025-02") → `ciclo_mudou = True` → bloco mensal executa.

## Arquivo
`run_server.py` — função `reset_historico_ativos()` chamada no `__main__`.

## Status
✅ Ativo — roda toda vez que o servidor inicia.
