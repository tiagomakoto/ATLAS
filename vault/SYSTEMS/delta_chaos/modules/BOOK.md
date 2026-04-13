---
uid: mod-delta-004
version: 1.2.1
status: validated
owner: Chan

function: Registro e auditoria de todas as posicoes abertas e fechadas. Calcula P&L, Sharpe, drawdown, sequencia de stops e breakdown por regime. Integra com Supabase.
file: delta_chaos/book.py
role: Repositorio de verdade operacional — todas as posicoes e metricas agregadas

input:
  - estrutura: dict — posicao aberta enviada pelo EDGE/FIRE
  - preco_fechamento: float — preco de saida no fechamento da posicao
  - slippage_aplicado: float — slippage real registrado no fechamento

output:
  - book_ativo: Parquet — historico de posicoes por ativo
  - dashboard: dict — Sharpe, drawdown, sequencia de stops, breakdown por regime, estado REFLECT
  - audit_log: JSON append-only — hash diario de integridade em BOOK_DIR/book_audit_log.json

depends_on:
  - [[SYSTEMS/delta_chaos/modules/TAPE]]
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]

depends_on_condition:

used_by:
  - [[SYSTEMS/delta_chaos/modules/EDGE]]

intent:
  - Registro imutavel e auditavel de toda a operacao. Audit log append-only — nunca sobrescrito.

constraints:
  - _salvar() atomico em paper/real — usa tempfile + os.replace()
  - _carregar() faz backup antes de reiniciar vazio + registra em audit_log
  - Parquet separado por ativo
  - Hash diario SHA-256 e SHA-512 — book_audit_log.json append-only em BOOK_DIR
  - Integracao Supabase — insercao automatica a cada trade fechado
  - fechar() aplica slippage_aplicado no P&L — nao ignora slippage

notes:
  - 2026-04-13: código modificado — book.py
  - Dashboard exibe Edge state, score e historico dos ultimos N estados por ativo
  - Tendencia dos componentes diarios no dashboard — implementacao pendente Chan
  - Q9 aberto: separar data_decisao de data_execucao antes da Fase live
  - B18 aberto: reconciliacao diaria com corretora nao automatizada
---
