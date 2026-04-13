---
uid: B48
title: Entrada close d0 vs open d1 — viés de simulação no TUNE
status: closed
opened_at: 2026-04-12
closed_at: 2026-04-12
opened_in: [[BOARD/atas/2026-04-12_tune_v2_escopo]]
closed_in: [[BOARD/atas/2026-04-12_tune_v2_escopo]]
decided_by: CEO
system: delta_chaos

description: >
  O TUNE v1.1 usa fechamento de d0 como preço de entrada da posição
  (premio_liq = melhor["fechamento"]). Na operação real, o CEO lê o
  sinal no EOD e executa no pré-mercado de d1 — preços distintos,
  especialmente em dias com gap de abertura. O backtest é
  sistematicamente otimista na entrada. Em dias de alta volatilidade
  — quando o sinal de entrada é mais forte — o gap entre fechamento
  e abertura é maior, amplificando o viés. Correção obrigatória
  antes de migração para capital real.

gatilho:
  - TUNE v2.0
  - obrigatório antes de capital real

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]

resolution: >
  Resolvido — sessão 2026-04-12.

  DIAGNÓSTICO FINAL:
  tune.py: sem bug. Fechamento d0 como proxy de abertura d1 é correto
  para backtest — é o melhor dado disponível para simular open d1.

  fire.py + book.py: bug confirmado e corrigido.
  O campo premio_entrada em Leg registrava sempre o fechamento d0.
  Em modo paper/real, o CEO executa no open d1 com preço diferente —
  a referência de P&L para gatilhos de TP/STOP estava incorreta.

  CORREÇÃO IMPLEMENTADA:
  - Leg recebe novo campo opcional `premio_executado` (book.py)
  - _leg() em fire.py inicializa premio_executado = None por padrão
  - verificar() em fire.py usa premio_executado como referência
    quando preenchido; fallback para premio_entrada (backtest/paper)
  - Serialização/deserialização atualizada em _op_to_dict/_dict_to_op
  - No modo real: preencher premio_executado via book após confirmação
    de execução pelo CEO

  Arquivos alterados: fire.py, book.py
  Backward compatible: premio_executado = None em todos os registros
  existentes — comportamento idêntico ao anterior.

notes:
  - Taleb: viés é maior em dias de vol elevada — exatamente quando o sinal é mais forte
  - Chan: premio_liq = melhor["fechamento"] — linha identificada no tune.py etapa 2
  - Correção: usar abertura de d1 como proxy de entrada — requer dado de abertura no TAPE
  - Verificar se GATE e FIRE têm o mesmo viés — impacto sistêmico provável
  - Conecta com B49 (slippage) — os dois são premissas de simulação interdependentes
---
