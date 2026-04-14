---
uid: B41
title: Delta alvo fixo — terceira variável de otimização do TUNE
status: open
opened_at: 2026-03-23
closed_at:
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in:
decided_by:
system: delta_chaos

description: >
  O delta alvo está fixo no sistema atual (ex: -0.29 no B0001).
  É a TERCEIRA variável de otimização do TUNE — ao lado de TP e Stop Loss.

  Enquanto TP e Stop Loss governam a SAÍDA da posição (quando fechar),
  o delta alvo governa a ENTRADA (onde abrir — qual strike escolher).
  As três juntas determinam o P&L esperado da estratégia.

  Delta alvo mais negativo (ex: -0.35) → strike mais próxima → prêmio maior →
  maior risco de toque no stop.
  Delta alvo menos negativo (ex: -0.20) → strike mais distante → prêmio menor →
  maior sobrevivência em movimentos adversos.

  A otimização das três variáveis simultaneamente via Optuna é o objetivo de Fase 2.
  O espaço de busca cresce materialmente com a adição do delta:
  range candidato [0.15, 0.35] step 0.05 → +5 valores → ~4.320 combinações totais.

acoplamentos_criticos:
  - delta alvo e TP/Stop NÃO são independentes — mudar a entrada muda o
    significado das saídas de forma não-linear
  - delta alvo se move com a superfície de vol — a mesma strike tem delta
    diferente conforme IV rank alto ou baixo
  - otimização global (sem segmentação por IV rank) produz resultado ilusório:
    mistura regimes de vol distintos como se fossem equivalentes
  - iv_rank por ciclo no ORBIT (entregue no TUNE v2.0 via ORBIT v3.6) é o
    pré-requisito técnico que estava faltando — agora existe

gatilho:
  - início da Fase 2
  - pré-requisito: acúmulo mínimo de dados de paper trading (ver B49)
  - pré-requisito cumprido: iv_rank por ciclo disponível no ORBIT v3.6

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/delta_chaos/modules/EDGE]]

resolution:

notes:
  - B0001 aberto com delta -0.29 — escolha operacional/intuitiva, não otimizada
  - Tensão localizada em sessão 2026-04-14 via busca no vault — descrição original
    era insuficiente para recuperação direta. Este registro foi reescrito para
    tornar o papel do delta alvo como terceira variável do TUNE explícito e
    imediatamente recuperável.
  - Conecta com: B42 (TUNE v2.0), B23 (critério parada Optuna), B47 (janela como
    hiperparâmetro), B49 (slippage e dados paper trading)
---
