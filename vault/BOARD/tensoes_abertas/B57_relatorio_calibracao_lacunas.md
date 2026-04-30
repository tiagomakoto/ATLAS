---
uid: B57
title: Relatório de calibração — lacunas de diagnóstico obrigatórias
status: open
opened_at: 2026-04-25
closed_at:
opened_in: [[BOARD/atas/2026-04-25_prio3_bloqueio_relatorio]]
closed_in:
decided_by: Board + CEO
system: atlas

description: >
  O relatório de calibração gerado pelo ATLAS (formato atual) carece de
  seis campos de diagnóstico identificados pelo board na análise de PRIO3
  (2026-04-25). Sem esses campos, o CEO não consegue contextualizar um
  bloqueio GATE sem análise manual adicional — o que contradiz o objetivo
  do relatório como documento autossuficiente de decisão.

  Lacunas identificadas (ordem de criticidade):

  1. DISTRIBUIÇÃO TEMPORAL DOS STOPS — em qual ciclo/ano ocorreram os
     stops consecutivos. É a informação mais crítica para distinguir
     bloqueio por condição recente vs. condição histórica superada.

  2. BREAKDOWN DE P&L POR ANO — P&L total da janela decomposto por ano
     calendário. Permite identificar se a janela está sendo dominada por
     um período atípico (ex: 2020 COVID, 2022 guerra).

  3. ESTADO REFLECT ATUAL — estado A/B/C/D/T do ativo após a calibração.
     Pós-B55, este é dado obrigatório em qualquer relatório que envolva
     o REFLECT.

  4. SIZING FINAL RECOMENDADO — sizing_orbit × sizing_reflect resultante
     do estado REFLECT. Deve aparecer mesmo quando bloqueado (valor
     hipotético "se desbloqueado"), para fins de auditoria e comparação
     entre calibrações.

  5. RECONCILIAÇÃO TUNE × GATE — diferença de N trades entre janela TUNE
     e janela GATE deve ser explicada (qual trade/ciclo está em um e não
     no outro). Quando a diferença muda o sinal do P&L médio, a nota
     de reconciliação é obrigatória.

  6. FREQUÊNCIA DE REGIMES NA JANELA — a tabela "Estratégia por regime"
     já presente no relatório deve ser complementada com a frequência
     relativa de cada regime na janela de backtest. Regime com 5% de
     ocorrência e regime com 60% têm pesos radicalmente diferentes na
     calibração.

gatilho:
  - implementação no gerador de relatório (ATLAS backend) dos seis campos
  - atualização do template de relatório .md em relatorios/
  - validação: próxima calibração de qualquer ativo deve conter todos os campos

impacted_modules:
  - [[SYSTEMS/atlas/modules/RELATORIOS]]
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]

resolution:

notes:
  - AUDITORIA SCAN 2026-04-29: nenhum dos 6 campos implementado. relatorios.py contém
    exportar_relatorio_calibracao() e gerar_relatorio_tune() mas sem distribuição temporal
    de stops, breakdown P&L por ano, estado REFLECT, sizing final, reconciliação TUNE×GATE
    ou frequência de regimes. Spec Lilian ainda não emitida. Campo 3 (estado REFLECT) depende
    de B55 estar totalmente implementado. Campos 4 (sizing final) depende de B56.
    Campos 1, 2, 5, 6 são independentes e implementáveis agora. Threshold para nota
    obrigatória no campo 5 (reconciliação TUNE×GATE) deve ir na spec de Lilian.

notes_originais:
  - Originado na análise de PRIO3 bloqueado em 2026-04-25: acerto 96%,
    2 stops consecutivos reverteram P&L total. Sem distribuição temporal,
    board não pôde determinar se bloqueio reflete condição recente ou histórica.
  - Dependência: B55 (estados REFLECT A/B/C/D/T) deve estar implementado
    antes de adicionar campo "estado REFLECT" ao relatório.
  - Campo 5 (reconciliação TUNE × GATE) é especialmente crítico quando
    a diferença de janela muda o sinal do P&L médio — caso exato do PRIO3.
---
