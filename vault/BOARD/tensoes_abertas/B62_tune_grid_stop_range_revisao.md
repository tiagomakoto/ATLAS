---
uid: B62
title: Grid Etapa A — range Stop 1.5–2.5 amplo demais para vendedor de vol
status: open
opened_at: 2026-04-29
closed_at:
opened_in: [[BOARD/atas/2026-04-29_tune_v31_arquitetura]]
closed_in:
decided_by:
system: delta_chaos

description: >
  O grid fixo aprovado para a Etapa A do TUNE v3.1 cobre Stop: [1.5, 2.0, 2.5].
  Range de 1.0x o prêmio é excessivamente amplo para um sistema vendedor de
  volatilidade — a diferença entre Stop=1.5 e Stop=2.5 não é granularidade de
  parâmetro, é diferença de filosofia de risco. Stop=1.5 sai no primeiro sinal
  de deterioração; Stop=2.5 absorve o dobro da perda antes de reagir.
  O grid atual foi aceito por ser empiricamente ancorado no histórico do sistema,
  mas com reconhecimento explícito de que o range de Stop precisa ser revisitado
  após acúmulo de dados de paper trading.

gatilho:
  - mínimo 1 trimestre de paper trading com TUNE v3.1 em produção
  - diagnóstico de distribuição de stops por nível (1.5 vs 2.0 vs 2.5) nos
    dados reais de paper trading
  - análise de Taleb sobre concentração de stops em eventos de cauda por nível

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/config/delta_chaos_config.json]] (tune.referencia_eleicao.stop_values)

resolution:

notes:
  - Tensão levantada por Taleb na sessão 2026-04-29. CEO concordou com a
    preocupação antes de fechar a SPEC do v3.1.
  - O grid não é hardcoded — está em config.json (tune.referencia_eleicao).
    Revisão não requer alteração de código, apenas de configuração.
  - Dependência: TUNE v3.1 implementado e validado (B61).
  - Hipótese de trabalho: range ideal de Stop pode ser 1.5–2.0 (eliminar 2.5)
    ou 1.75–2.25 (centralizar com passo menor). Requer dados para decidir.
---
