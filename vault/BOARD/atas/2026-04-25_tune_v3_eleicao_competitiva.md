---
date: 2026-04-25
session_type: board
system: delta_chaos

decisions:
  - id: D01
    o_que: TUNE v3.0 escopo restrito a seleção de estratégia por regime — TP/STOP globais preservados
    porque: Manter entrega cirúrgica. FIRE/GATE/BOOK leem TP/STOP em 6+ pontos — migração é escopo 2x maior e requer validação separada.
    rejeitado: v3.0 completa (TP/STOP por regime) — escopo excessivo; v3.0 com média ponderada — matematicamente incoerente (Thorp)

  - id: D02
    o_que: Posições abertas preservam snapshot de estratégia/TP/STOP da abertura
    porque: Alterar parâmetros retroativamente muda regras no meio da operação. Em capital real é erro operacional grave.
    rejeitado: Herdar imediatamente — pode gerar saída forçada se novo TP < P&L atual

  - id: D03
    o_que: Candidatos admissíveis por regime definidos em config.json — nunca hardcoded
    porque: Parâmetros empíricos provisórios (PE-008) devem ser revisáveis sem alteração de código.
    rejeitado: Hardcoded em tune.py — impede revisão sem deploy

  - id: D04
    o_que: Legacy deprecado na mesma entrega — executar_tune, tune_aplicar_estrategias, POST /tune/aplicar, TuneApprovalCard.jsx
    porque: Dual com flag aumenta superfície de erro sem benefício real dado que paper trading pode absorver rollback manual.
    rejeitado: Dual com flag (opção recomendada pelo coder) — CEO optou por deprecação imediata dado contexto de paper trading

  - id: D05
    o_que: N mínimo para eleição competitiva = 15 trades por regime (PE-008)
    porque: Abaixo de 15 o Optuna não discrimina candidatos com confiança mínima. Mandelbrot: N efetivo é menor que N aparente por clustering temporal.
    rejeitado: N=30 (conservador demais, bloquearia maioria dos regimes); sem threshold (overfitting garantido)

  - id: D06
    o_que: Máscara REFLECT global por regime — idêntica para todos os candidatos do mesmo regime
    porque: Estado REFLECT é condição do ativo, não da estratégia. BCS e BPS enfrentam a mesma condição externa no mesmo ciclo.
    rejeitado: Máscara estratégia-específica — complexidade desnecessária, Derman retirou a tensão após esclarecimento do CEO

  - id: D07
    o_que: Ranking completo inescapável na UI — confirmação por regime, não global
    porque: Apresentar só o vencedor comprime espaço de dúvida legítima (Douglas). CEO precisa ver N trades e IR de cada candidato antes de confirmar.
    rejeitado: Confirmação global — auditoria insuficiente

tensoes_abertas:
  - [[BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva]]
  - [[BOARD/tensoes_abertas/B60_neutro_consolidacao]]
  - [[BOARD/tensoes_abertas/B61_tune_v31_tp_stop_por_regime]]

tensoes_fechadas:

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/atlas/modules/CalibracaoDrawer]]

next_actions:
  - Dalio: PE-008 em principios_empiricos.md
  - Dalio: B59, B60, B61 em decision_log.md
  - Chan: Fase 1 e Fase 2 do plano (vault + config) podem iniciar imediatamente
  - Chan: Fase 3 condicionada às três condições SCAN (C1, C2, C3)
---

# Ata — 2026-04-25 — TUNE v3.0: eleição competitiva de estratégia por regime

## Contexto
Sessão motivada pela pergunta do CEO: o Optuna deveria identificar melhores
estratégias por regime, além de TP/STOP. Board deliberou em duas rodadas sobre
tabela de candidatos admissíveis, threshold N mínimo e escopo da entrega.
SCAN aprovou plano com três condições antes da Fase 3.

## Decisões

### D01 — Escopo v3.0 restrito a seleção de estratégia
**O que:** TUNE v3.0 elege estratégia por regime. TP/STOP globais preservados. FIRE/GATE/BOOK não mudam.
**Por quê:** Entrega cirúrgica. Migração TP/STOP é escopo 2x maior — B61.
**Rejeitado:** v3.0 completa (escopo excessivo); média ponderada de TP/STOP (incoerente — Thorp).

### D02 — Snapshot na entrada para posições abertas
**O que:** Posições paper/real preservam estratégia/TP/STOP do momento da abertura. Calibração nova afeta só posições futuras.
**Por quê:** Alterar retroativamente é erro operacional. Em capital real, pode gerar saída forçada indevida.
**Rejeitado:** Herdar imediatamente.

### D03 — Candidatos em config.json, nunca hardcoded
**O que:** Tabela de candidatos admissíveis por regime em delta_chaos_config.json com comentários PE-008.
**Por quê:** Parâmetros empíricos provisórios devem ser revisáveis sem deploy.
**Rejeitado:** Hardcoded em tune.py.

### D04 — Legacy deprecado imediato
**O que:** executar_tune, tune_aplicar_estrategias, POST /tune/aplicar e TuneApprovalCard.jsx removidos na mesma entrega.
**Por quê:** CEO optou por depreciação imediata dado contexto de paper trading com rollback manual viável.
**Rejeitado:** Dual com flag (opção recomendada pelo coder).

### D05 — N mínimo = 15 trades por regime (PE-008)
**O que:** Regimes com N < 15 usam candidato estrutural fixo sem eleição competitiva.
**Por quê:** Abaixo de 15, Optuna não discrimina candidatos com confiança mínima. Clustering temporal reduz N efetivo (Mandelbrot).
**Rejeitado:** N=30 (bloquearia maioria dos regimes); sem threshold.

### D06 — Máscara REFLECT global por regime
**O que:** Máscara idêntica para todos os candidatos do mesmo regime.
**Por quê:** Estado REFLECT é condição do ativo. CEO esclareceu: jogo excluído é condição extra-campo — igual para os dois times.
**Rejeitado:** Máscara estratégia-específica — Derman retirou a tensão após esclarecimento.

### D07 — Ranking inescapável, confirmação por regime
**O que:** UI exibe ranking completo sem colapso. Confirmação é por regime, não global.
**Por quê:** Douglas: fechamento prematuro é risco comportamental real. CEO precisa ver o ranking completo antes de confirmar.
**Rejeitado:** Confirmação global.

## Tensões abertas desta sessão
- [[BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva]]
- [[BOARD/tensoes_abertas/B60_neutro_consolidacao]]
- [[BOARD/tensoes_abertas/B61_tune_v31_tp_stop_por_regime]]

## Condições SCAN antes da Fase 3
- C1: passo 6b — contingência explícita se auditoria D12 falhar em book.py
- C2: dry-run mode no migration script (passo 11)
- C3: grep de NEUTRO documentado como checklist do passo 8
