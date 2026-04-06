# DEBUG_TICKER — Limitar orquestrador a um ativo

## Contexto
O orquestrador roda em loop por todos os ativos parametrizados. Para debug, isso é lento e dificulta identificar bugs.

## Decisão
Adicionar flag `DEBUG_TICKER` em `delta_chaos.py` (linha ~223):
```python
DEBUG_TICKER = "VALE3"  # None = roda todos
```

## Por quê
Permite testar o fluxo completo com um único ativo, acelerando o ciclo de debug.

## Como desativar
Voltar para `DEBUG_TICKER = None`.

## Arquivo
`atlas_backend/api/routes/delta_chaos.py`

## Status
✅ Ativo — configurado para `VALE3`.
