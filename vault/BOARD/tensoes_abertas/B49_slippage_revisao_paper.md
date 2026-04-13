---
uid: B49
title: Slippage 10% — revisão após dados reais de paper trading
status: open
opened_at: 2026-04-12
closed_at:
opened_in: [[BOARD/atas/2026-04-12_tune_v2_escopo]]
closed_in:
decided_by:
system: delta_chaos

description: >
  O slippage de 10% usado na simulação do TUNE é provisório —
  definido sem base empírica de execução real. Com paper trading
  ativo, o CEO acumula dados de prêmio alvo vs prêmio executado
  por ativo. Após primeiro trimestre, revisar o slippage com base
  empírica por ativo. Valor atual pode super ou subestimar o
  custo real de execução dependendo do ativo e do regime de liquidez.

gatilho:
  - fim do primeiro trimestre de paper trading
  - mínimo 10 trades executados por ativo para base empírica

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]

resolution:

notes:
  - Eifert: paper trading deve registrar prêmio alvo vs executado por trade
  - Slippage pode variar por ativo — BOVA11 mais líquido que BBAS3
  - Conecta com B48 (close d0 vs open d1) — premissas de simulação interdependentes
  - Valor 10% pode estar embutido em PREMIO_MIN ou sizing — Chan deve localizar exato
---
