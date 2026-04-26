---
uid: B61
title: TUNE v3.1 — TP/STOP por regime + migração FIRE/GATE/BOOK
status: open
opened_at: 2026-04-25
closed_at:
opened_in: [[BOARD/atas/2026-04-25_tune_v3_eleicao_competitiva]]
closed_in:
decided_by: Board + CEO
system: delta_chaos

description: >
  O TUNE v3.0 grava a estratégia eleita por regime mas mantém TP/STOP globais
  (take_profit/stop_loss no JSON do ativo). FIRE, GATE e BOOK leem TP/STOP
  em 6+ pontos usando os campos globais.

  A próxima evolução natural é TP/STOP por regime — cada regime com parâmetros
  de saída calibrados independentemente. Esta tensão registra o escopo
  deliberadamente excluído do v3.0 para manter a entrega cirúrgica.

  Escopo v3.1:
  - TUNE persiste tp_por_regime e stop_por_regime no JSON do ativo
  - FIRE, GATE e BOOK migram para ler TP/STOP do regime da posição na entrada
  - Snapshot D12 garante que posições abertas preservam TP/STOP da abertura
  - Migration script: ativos v3.0 ganham tp_por_regime/stop_por_regime derivados
    do TP/STOP global atual (todos os regimes com o mesmo valor inicial)

gatilho:
  - validação completa do TUNE v3.0 em paper trading (mínimo 1 ciclo por ativo)
  - diagnóstico de variância de TP/STOP ótimo entre regimes (dados do ranking
    tune_ranking_estrategia disponíveis após v3.0)
  - decisão do board sobre escopo e sequência

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]
  - [[SYSTEMS/delta_chaos/modules/BOOK]]
  - [[SYSTEMS/atlas/modules/CalibracaoDrawer]]

resolution:

notes:
  - Dependência: TUNE v3.0 implementado e validado.
  - Os dados de TP/STOP por candidato já estarão disponíveis no
    tune_ranking_estrategia após v3.0 — servem como base analítica
    para justificar ou não a migração.
  - Escopo ~2x maior que v3.0 por conta da migração FIRE/GATE/BOOK.
---
