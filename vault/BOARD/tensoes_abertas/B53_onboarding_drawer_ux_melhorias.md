---
uid: B53
title: CalibraçãoDrawer — reformulação estrutural (v3.0)
status: open
opened_at: 2026-04-14
closed_at:
opened_in: [[BOARD/atas/2026-04-14_atlas_websocket_onboarding_ux]]
closed_in:
decided_by:
system: atlas

description: >
  Drawer de calibração funcional confirmado em uso real (PETR4, step 1 concluído).
  Reformulação estrutural aprovada pelo board em 2026-04-17 cobre 9 itens:
  (1) Bug: numeração dos steps no resumo do topo incorreta — corrigir.
  (2) Remover bloco de resumo do topo — redundante com os cards.
  (3) Nome técnico da etapa em cada card (backtest_dados, tune, gate + fire).
  (4) Próximo step destacado em azul sutil; label muda de PENDENTE para PRÓXIMO.
  (5) Duração calculada no card concluído (iniciado_em → concluido_em).
  (6) Descrição prévia no card TUNE quando próximo: "Optuna 200 trials · estimativa 4–8h".
  (7) Renomear drawer e componente de "Onboarding" para "Calibração" — fluxo cobre
  tanto ativo novo quanto re-calibração de ativo já operacional. Fluxo único
  invariante: backtest_dados → TUNE → GATE. Decisão unânime do board.
  (8) Guard de dados recentes no step 1: se dados < 7 dias, oferecer opção de pular.
  (9) Step 3 reformulado: GATE com pass/fail granular por critério (8 critérios
  individuais visíveis); FIRE dispara somente após GATE pass, exibindo diagnóstico
  histórico por regime (trades, acerto, IR isolado, worst trade, estratégia dominante,
  cobertura, distribuição de stops); relatório exportável em .md ao final.
  SPEC_CALIBRACAO_DRAWER_v3.0.md emitida por Lilian — substitui specs anteriores.

gatilho:
  - CEO entrega SPEC_CALIBRACAO_DRAWER_v3.0.md ao PLAN do OpenCode

impacted_modules:
  - atlas_ui/src/components/GestaoView/CalibraçãoDrawer.jsx (renomeado de OnboardingDrawer)
  - atlas_ui/src/components/GestaoView/GestaoView.jsx (atualizar import)
  - atlas_backend/api/routes/ (novos endpoints gate-resultado e fire-diagnostico)

resolution:

notes:
  - Itens 1–6: melhorias visuais — lógica de WebSocket e watchdog preservados da v2.0
  - Item 7: renomeação de componente — GestaoView.jsx atualiza import
  - Item 8: guard de dados recentes — read-only no master JSON, sem escrita
  - Item 9: GATE granular + FIRE diagnóstico — dois novos endpoints backend (read-only)
  - FIRE não é step bloqueante — é painel de inteligência que só aparece após GATE pass
  - Spec substitui SPEC_ONBOARDING_DRAWER_v2.0.md e SPEC_ONBOARDING_DRAWER_UX_v1.0.md
  - SPEC_RELATORIO_TUNE_v1.0.md (B51) permanece independente — aba do ativo, não drawer
---
