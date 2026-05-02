---
date: 2026-04-30
session_type: off-ata
system: delta_chaos

decisions:
  - id: D01
    o_que: Fechamento de B63 — patch cirúrgico delta_chaos_config.json v1.4 aplicado e verificado
    porque: >
      SCAN auditou orbit.py, tune.py e delta_chaos_config.json via MCP e identificou
      que o coder havia migrado apenas orbit.py. O config permanecia com 10 rótulos
      NEUTRO_* como fonte de verdade do TUNE, causando zero trades em LATERAL_BULL/
      LATERAL_BEAR/LATERAL na tela de MGLU3. Patch cirúrgico aplicado em 4 seções.
      CEO confirmou checklist de 7 itens ✅ em G Drive e Local antes do fechamento.
    rejeitado: >
      Reescrita completa do config — rejeitada. Patch cirúrgico nas 3 seções afetadas
      é suficiente e minimiza risco de regressão em seções não relacionadas.

  - id: D02
    o_que: Fechamento de B38 por obsolescência — NEUTRO_TRANSICAO eliminado por B63
    porque: >
      B38 requeria definição de estratégia para NEUTRO_TRANSICAO. Com B63 aprovada,
      o regime foi eliminado do universo (artefato de fronteira ORBIT, não regime de
      mercado real). Não há estratégia a definir — tensão resolvida por eliminação
      do problema.
    rejeitado: n/a

tensoes_abertas: []

tensoes_fechadas:
  - [[BOARD/decisoes/B63_regimes_renomeacao_lateral]]
  - [[BOARD/decisoes/B38_BOVA11_NEUTRO_TRANSICAO]]

impacted_modules:
  - delta_chaos_config.json
  - orbit.py (já migrado)

next_actions:
  - Hard reset dos JSONs de todos os ativos (tune_ranking_estrategia com chaves NEUTRO_*)
  - Re-TUNE de todos os ativos com config v1.4
  - Onboarding de MGLU3 rerrodar após hard reset
---

# Ata — 2026-04-30 — Fechamento B63 — Regimes LATERAL_*

## Contexto
MGLU3 onboardado exibiu 10 regimes antigos (NEUTRO_*) na tela de TUNE.
SCAN auditou os três arquivos críticos via MCP e identificou mismatch:
orbit.py migrado corretamente; delta_chaos_config.json permanecia com
nomenclatura pré-B63. Patch cirúrgico aplicado e verificado pelo CEO.

## Decisões

### D01 — Fechamento B63 — patch config.json v1.4
**O que:** Patch cirúrgico em delta_chaos_config.json v1.4 — 4 seções migradas para 7 rótulos LATERAL_*.
**Por quê:** SCAN identificou via leitura direta que tune.candidatos_por_regime, tune.estrategia_estrutural_fixo, fire.regime_estrategia e fire.regimes_sizing_padrao mantinham nomenclatura NEUTRO_*. O TUNE itera sobre as chaves do config como fonte de verdade — sem migração, encontrava zero trades em LATERAL_* porque buscava NEUTRO_* no historico[], que já gravava LATERAL_* desde a migração do orbit.py.
**Rejeitado:** Reescrita completa do config — risco de regressão desnecessário.

### D02 — Fechamento B38 por obsolescência
**O que:** B38 (BOVA11 NEUTRO_TRANSICAO sem estratégia) fechada por obsolescência.
**Por quê:** NEUTRO_TRANSICAO eliminado do universo de regimes por B63. Regime era artefato de fronteira do ORBIT (~7% frequência constante em todos os ativos), redistribuído para LATERAL via _redistribuir_transicao em orbit.py.
**Rejeitado:** n/a

## Tensões fechadas desta sessão
- [[BOARD/decisoes/B63_regimes_renomeacao_lateral]]
- [[BOARD/decisoes/B38_BOVA11_NEUTRO_TRANSICAO]]
