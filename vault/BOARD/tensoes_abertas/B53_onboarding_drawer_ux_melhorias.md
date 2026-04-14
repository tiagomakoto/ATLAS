---
uid: B53
title: CalibraçãoDrawer — melhorias de UX/UI (8 itens)
status: open
opened_at: 2026-04-14
closed_at:
opened_in: [[BOARD/atas/2026-04-14_atlas_websocket_onboarding_ux]]
closed_in:
decided_by:
system: atlas

description: >
  Drawer de calibração funcional confirmado em uso real (PETR4, step 1 concluído).
  Oito melhorias identificadas pelo board:
  (1) Bug: numeração dos steps no resumo do topo incorreta — ambos pendentes
  mostram "Step 2" em vez de "Step 2" e "Step 3".
  (2) Remover bloco de resumo do topo — redundante com os cards.
  (3) Nome técnico da etapa em cada card (backtest_dados, tune, backtest_gate).
  (4) Próximo step destacado em azul sutil em vez de cinza idêntico aos demais.
  (5) Duração calculada no card concluído (iniciado_em → concluido_em).
  (6) Descrição prévia no card TUNE quando pendente: "Optuna 200 trials · estimativa 4–8h".
  (7) Renomear drawer e componente de "Onboarding" para "Calibração" — fluxo cobre
  tanto ativo novo quanto re-calibração de ativo já operacional; nome "Onboarding"
  implica ação única e está incorreto. Decisão do board: fluxo único invariante
  (backtest_dados → TUNE → GATE), independente do contexto de uso.
  (8) Step 1 (backtest_dados) deve incluir guard de dados recentes: se dados já
  atualizados, exibir "Dados atualizados em DD/MM — deseja rodar mesmo assim?"
  com opção de pular — dentro do mesmo fluxo, não fluxo separado.
  SPEC_ONBOARDING_DRAWER_UX_v1.0.md emitida por Lilian (itens 1–6) — aguarda PLAN.
  Itens 7 e 8 adicionados em sessão de 2026-04-14 — requerem nova spec de Lilian.

gatilho:
  - Implementação aprovada pelo CEO e entregue ao PLAN

impacted_modules:
  - atlas_ui/src/components/GestaoView/OnboardingDrawer.jsx
  - atlas_ui/src/components/GestaoView/CalibraçãoDrawer.jsx (renomeado)

resolution:

notes:
  - Itens 1–6: apenas mudanças visuais — lógica de WebSocket, parsing de eventos e watchdog não tocados
  - Itens 7–8: renomeação de componente + guard de dados — requerem spec complementar de Lilian
  - Spec original produzida por Lilian em 2026-04-14 baseada em screenshot de uso real
  - Decisão de fluxo único ratificada por board em 2026-04-14: mesma sequência para ativo novo e re-calibração
---
