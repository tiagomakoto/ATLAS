---
uid: B64
title: PETR4/ITUB4 historico duplicado — bug em tape_ciclo_salvar (c09af5e)
status: open
opened_at: 2026-04-29
closed_at:
opened_in: [[BOARD/atas/2026-04-29_regimes_nomenclatura_lateral]]
closed_in:
decided_by:
system: delta_chaos

description: >
  PETR4.json apresentava 1125 entradas em historico[] com apenas 288 ciclo_ids
  únicos (~3.9x de duplicação). Corrigido manualmente via deduplicate_petr4.py
  (2026-04-29). ITUB4.json ainda apresenta 561/276 ciclos (fator 2.03x, máx
  3 repetições por ciclo_id) — 262 ciclos duplicados, de 2003-05 a 2025-02.

## DIAGNÓSTICO — 2026-04-29

### Vetor causador identificado: commit c09af5e

Refactor "Renomeação canônica de funções" introduziu o seguinte bug em
`delta_chaos/tape.py`, função `tape_ciclo_salvar`:

```python
# VERSÃO BUGADA (c09af5e):
if registro_existente.get("definitivo", True):
    pass  # ← NÃO removia o registro existente!
else:
    dados["historico"] = [c for c in dados["historico"]
                          if c.get("ciclo_id") != ciclo_id]
dados["historico"].append(resultado)
```

Quando `registro_existente = {}` (ciclo não existia) ou `definitivo=True`,
o código fazia `pass` e depois `append` — duplicava em vez de substituir.
Na prática, toda execução de `dc_orbit` com anos=[2002..2026] chamava
`tape_ciclo_salvar` para cada um dos ~288 ciclos históricos, acumulando
cópias exatas a cada rerrodada.

Corrigido em commit subsequente (735d249 ou anterior) para o padrão atual
de ambos os branches removerendo por ciclo_id antes do append. A correção
foi aplicada no código mas os JSONs já estavam corrompidos.

### Escopo da corrupção (fator de duplicação por ativo, 2026-04-29)

| Ativo | Total | Únicos | Fator | Status |
|-------|-------|--------|-------|--------|
| BBAS3 | 288 | 288 | 1.00x | Limpo |
| BBDC4 | 190 | 190 | 1.00x | Limpo |
| BOVA11 | 174 | 174 | 1.00x | Limpo |
| ITUB4 | 561 | 276 | 2.03x | **CORROMPIDO** |
| PETR4 | 288 | 288 | 1.00x | Corrigido (manualmente) |
| PRIO3 | 156 | 156 | 1.00x | Limpo |
| VALE3 | 288 | 288 | 1.00x | Limpo |

### O que NÃO é o vetor

- `orbit.py` — apenas lê `historico[]`, não escreve diretamente.
- `run_server.py` — função `reset_historico_ativos()` comentada; e só REMOVE.
- `migrate_regime.py` — só renomeia campo `regime_estrategia → regime`.
- Race condition — audit.log mostra execuções paralelas ocasionais, mas
  o padrão de ~2-4x é consistente com rerrodadas sequenciais do ORBIT,
  não com race condition.

### Guarda atual (tape.py:522-538)

A versão atual está funcionalmente correta mas tem if/else redundante:
ambos os branches removem por ciclo_id antes do append. A simplificação
está na SPEC_B64_v2 (não nesta tensão).

gatilho:
  - imediato — ITUB4 ainda corrompido; próxima rerrodada de ORBIT pode
    re-corromper PETR4 se a guarda atual não funcionar conforme esperado
    (verificar com teste de regressão)

impacted_modules:
  - delta_chaos/tape.py (tape_ciclo_salvar, linhas 514-565)
  - G:/Meu Drive/Delta Chaos/ativos/ITUB4.json (561 entradas, 276 únicas)

resolution: >
  Pendente. Requer SPEC_B64_v2 com:
  1. Deduplicar ITUB4.json por ciclo_id (não por data_ref como PETR4).
  2. Refatorar tape_ciclo_salvar (522-538) para o pseudo-código limpo
     (find-by-id + update-in-place vs append), preservando sort por ciclo_id.
  3. Adicionar teste de regressão: tape_ciclo_salvar chamado 2x com mesmo
     ciclo_id → len(historico) == 1.

notes:
  - PETR4 corrigido por deduplicate_petr4.py (usou data_ref como chave).
    Para ITUB4 usar ciclo_id como chave primária conforme a SPEC.
  - Não há backup .bak_* disponível para análise retrospectiva (migrate_regime
    não foi rodado nos ativos afetados ou backup foi removido).
  - audit.log confirma múltiplas execuções de dc_orbit com anos=[2002..2026]
    em 2026-04-13 (sessão de diagnóstico intenso). Vetor histórico já extinto
    no código — guarda atual funciona, mas JSONs foram corrompidos no passado.
---
