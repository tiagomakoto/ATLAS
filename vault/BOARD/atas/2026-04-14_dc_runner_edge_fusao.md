---
date: 2026-04-14
session_type: board
system: atlas

decisions:
  - Arquitetura de subprocess eliminada — dc_runner.py passa a importar edge.py como módulo Python diretamente
  - Comunicação via JSONL temporário (emit_event + _watch_events_inner + _flush_events) removida
  - emit_dc_event substitui emit_event em edge.py — mesmo processo, mesmo loop uvicorn
  - emit_log/emit_error em edge.py migram para importação direta de atlas_backend.core.terminal_stream
  - Cada chamada a edge.* em dc_runner envolve try/except com emit de erro estruturado por estágio
  - asyncio.to_thread() preservado em todos os wrappers async — funções de edge.py são bloqueantes
  - Polling SQLite para TUNE mantido intacto — independe do modelo subprocess
  - Bloco if __name__ == "__main__" em edge.py mantido para uso manual/debug futuro
  - SCAN auditou e incorporou três adendos obrigatórios à spec antes de liberação ao código
  - Spec emitida por Lilian — B54 aberta

tensoes_abertas:
  - [[BOARD/tensoes_abertas/B54_dc_runner_edge_import_direto]]

tensoes_fechadas:

impacted_modules:
  - atlas_backend/core/dc_runner.py
  - delta_chaos/edge.py

next_actions:
  - CEO entrega spec ao PLAN (B54)
---

# Ata — 2026-04-14 — dc_runner: eliminação de subprocess, import direto de edge.py

## Contexto

Sessão iniciada por questão arquitetural do CEO: o subprocesso lançado pelo dc_runner.py
para executar edge.py constitui violação de separação de responsabilidades? A resposta
do board foi afirmativa. A sessão evoluiu para decisão de migração completa para import direto.

## Diagnóstico arquitetural

Board identificou três problemas no modelo subprocess atual:

**Dois orquestradores coexistindo:** edge.py foi o orquestrador original do Colab. Com
a migração para ATLAS, dc_runner.py assumiu esse papel. Manter edge.py como processo
filho cria ambiguidade de responsabilidade permanente.

**Canal lateral de comunicação:** subprocesso comunicava com o frontend via arquivo JSONL
temporário lido por thread paralela (_watch_events_inner). Modelo frágil e indireto.
Parcialmente corrigido na sessão anterior (14/04 manhã), mas estruturalmente incorreto.

**Isolamento de processo desnecessário:** único benefício real de subprocess é isolamento
de falha. Board avaliou que try/except por estágio oferece proteção equivalente com
menor complexidade. Confirmado pelo CEO: edge.py não é mais executado standalone fora do ATLAS.

## Decisão

Opção C aprovada por unanimidade técnica: dc_runner.py importa edge.py como módulo Python.
Sem subprocess, sem JSONL, sem _watch_events_inner. Lilian emitiu spec completa com
adendos SCAN incorporados.

## Adendos SCAN (obrigatórios na implementação)

1. emit_event → emit_dc_event com mapeamento explícito start/done/error
2. Bloco __main__ em edge.py: manter (não remover)
3. asyncio.to_thread() obrigatório em todos os wrappers async que chamam edge.*

## Tensões desta sessão

- [[BOARD/tensoes_abertas/B54_dc_runner_edge_import_direto]]
