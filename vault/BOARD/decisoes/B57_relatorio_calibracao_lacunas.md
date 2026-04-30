---
uid: B57
title: Relatório de calibração — lacunas de diagnóstico obrigatórias
status: closed
opened_at: 2026-04-25
closed_at: 2026-04-29
opened_in: [[BOARD/atas/2026-04-25_prio3_bloqueio_relatorio]]
closed_in: [[BOARD/atas/2026-04-29_fechamento_b53_b54_b55_b56_b57]]
decided_by: Board + CEO
system: atlas

description: >
  O relatório de calibração gerado pelo ATLAS carecia de seis campos de diagnóstico
  identificados na análise de PRIO3 (2026-04-25). Sem esses campos, o CEO não consegue
  contextualizar um bloqueio GATE sem análise manual adicional.

gatilho:
  - implementação no gerador de relatório dos seis campos
  - atualização do template de relatório .md
  - validação: próxima calibração deve conter todos os campos

impacted_modules:
  - [[SYSTEMS/atlas/modules/RELATORIOS]]
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]

resolution: >
  Implementado. formatar_relatorio_markdown() em relatorios.py contém as 5 seções
  novas após "Distribuição de saídas": Distribuição temporal de stops (campo 1),
  P&L por ano com N trades por linha (campo 2), Frequência de regimes (campo 6),
  Estado REFLECT atual com sizing_final (campo 3+4), Reconciliação TUNE×GATE com
  nota obrigatória condicional via nota_obrigatoria_b57 (campo 5). gerar_relatorio_tune()
  extrai stops_por_ano, pnl_por_ano, freq_regimes, reflect_state_atual, sizing_final,
  e diferenca_tune_gate. Todos os campos têm fallback para dados ausentes.
  Ressalva SCAN: critério de ativação de nota_obrigatoria_b57 (threshold 0.5 + sign flip)
  não verificado diretamente — tratado como PE provisório até próxima calibração real.
  Suite 76/76 verde. SCAN aprovado 2026-04-29 com ressalva menor documentada.

notes:
  - Threshold 0.5 para nota_obrigatoria_b57 é provisório — calibrar após primeira
    calibração real que acione o campo
  - Campo 3 (reflect_state) e campo 4 (sizing_final) dependiam de B55/B56 — ambos
    fechados na mesma sessão, sequência respeitada
  - AUDITORIA SCAN 2026-04-29: APROVADO ✅ com ressalva menor (threshold campo 5)
---
