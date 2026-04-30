---
uid: B53
title: CalibraçãoDrawer — reformulação estrutural (v3.0)
status: closed
opened_at: 2026-04-14
closed_at: 2026-04-29
opened_in: [[BOARD/atas/2026-04-14_atlas_websocket_onboarding_ux]]
closed_in: [[BOARD/atas/2026-04-29_fechamento_b53_b54_b55_b56_b57]]
decided_by: Board + CEO
system: atlas

description: >
  Drawer de calibração reformulado estruturalmente em 9 itens aprovados em 2026-04-17.
  Cobertura: renomeação Onboarding→Calibração, steps com status visual completo,
  guard de dados recentes, GATE granular 8 critérios, FIRE diagnóstico por regime,
  exportação .md, badge N<5 no painel FIRE.

gatilho:
  - CEO entrega SPEC_CALIBRACAO_DRAWER_v3.0.md ao PLAN do OpenCode

impacted_modules:
  - atlas_ui/src/components/GestaoView/CalibraçãoDrawer.jsx
  - atlas_ui/src/components/GestaoView/GestaoView.jsx
  - atlas_backend/api/routes/

resolution: >
  Implementado. Componente renomeado CalibracaoDrawer.jsx. GestaoView.jsx importa
  CalibracaoDrawer (zero referências a OnboardingDrawer confirmadas). 3 steps com
  status visual (PENDENTE/PRÓXIMO/EXECUTANDO/CONCLUÍDO/ERRO/PAUSADO), label PRÓXIMO
  em azul, duração por card, descrição prévia TUNE. Guard step 1 implementado com
  opções Pular/Rodar mesmo assim. GATE granular com 8 critérios individuais pass/fail
  progressivos via WebSocket. FIRE diagnóstico por regime com trades, acerto, IR,
  worst trade. Badge ⚠ N<5 em amber inline após IR para regimes com menos de 5 trades.
  Botão exportar .md presente. Suite 76/76 verde. SCAN aprovado 2026-04-29.

notes:
  - SPEC_CALIBRACAO_DRAWER_v3.0.md substitui SPEC_ONBOARDING_DRAWER_v2.0.md e
    SPEC_ONBOARDING_DRAWER_UX_v1.0.md — consideradas encerradas
  - SPEC_RELATORIO_TUNE_v1.0.md (B51) permanece independente — aba do ativo, não drawer
  - AUDITORIA SCAN 2026-04-29: APROVADO ✅
---
