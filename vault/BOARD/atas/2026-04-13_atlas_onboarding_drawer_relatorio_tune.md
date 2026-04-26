---
date: 2026-04-13
session_type: board
system: atlas

decisions:
  - id: D01
    o_que: Relatório de TUNE vive na aba "Relatórios" do NAV inline do Ativo — não em dropdown na aba Gestão
    porque: Gestão é manutenção (onboarding, calibração, parâmetros). Ativo é onde o CEO extrai todos os dados daquele ticker. Relatório de calibração é dado do ativo, não operação de gestão.
    rejeitado: Dropdown em Gestão — rejeitado pelo CEO porque mistura leitura com operação; Gestão deve ser reservada para ações, não consulta.

  - id: D02
    o_que: A aba "Relatórios" no NAV inline do Ativo é o único ponto de acesso a relatórios de calibração por ativo
    porque: Centraliza consulta sem duplicar com RelatorioTab (que lista todos os ativos globalmente em outra view).
    rejeitado: Seção inline dentro da AtivoView sem NAV — rejeitado por agravar o monolito de 62KB sem estrutura de navegação.

  - id: D03
    o_que: Relatórios são documentos exportáveis gerados em disco (.md) — não resumos computados on-demand
    porque: relatorios.py já gera e persiste .md com index.json. A aba consome o que existe em disco, não recalcula.
    rejeitado: Resumos computados on-demand — rejeitado por redundância com o que o backend já entrega e por aumentar acoplamento desnecessariamente.

  - id: D04
    o_que: B51 aberta — SPEC_RELATORIO_TUNE_v1.0.md a ser emitida por Lilian
    porque: Decisões D01–D03 estão consolidadas e prontas para especificação.
    rejeitado: —

tensoes_abertas:
  - [[BOARD/tensoes_abertas/B50_drawer_onboarding_estado_persistido]]
  - [[BOARD/tensoes_abertas/B51_nav_relatorio_tune_exportavel]]
  - [[BOARD/tensoes_abertas/B52_tp_stop_ativos_table]]

tensoes_fechadas:

impacted_modules:
  - [[SYSTEMS/atlas/modules/AtivoView]]
  - [[SYSTEMS/atlas/modules/RelatorioTab]]
  - [[SYSTEMS/atlas/modules/relatorios]]
  - [[SYSTEMS/atlas/modules/GestaoView]]

next_actions:
  - Lilian emitir SPEC_RELATORIO_TUNE_v1.0.md para PLAN (B51)
  - Lilian emitir spec de estado persistido no master JSON para drawer (B50)
  - Lilian emitir spec de TP/STOP visível na AtivosTable (B52)
---

# Ata — 2026-04-13 — ATLAS: drawer onboarding + relatório TUNE

## Contexto

Sessão focada em três demandas de ATLAS: persistência de estado do drawer de onboarding
no master JSON, onde vive o relatório de TUNE por ativo, e visibilidade de TP/STOP na
tabela de ativos. Ata reconstruída em 2026-04-25 — arquivo original não foi criado em disco.

## Decisões

### D01 — Relatório TUNE vive no NAV inline do Ativo, não em Gestão
**O que:** A aba "Relatórios" do NAV inline do Ativo é o ponto de acesso aos relatórios de calibração por ticker.
**Por quê:** Gestão é reservada para operações (onboarding, calibração, aplicação de parâmetros). Ativo é onde o CEO extrai todos os dados de um ticker. Relatório de calibração é dado do ativo.
**Rejeitado:** Dropdown em Gestão — mistura leitura com operação; CEO rejeitou explicitamente.

### D02 — NAV inline do Ativo como estrutura de navegação
**O que:** A aba Relatórios existe dentro do NAV inline do Ativo como seção dedicada, distinta das abas ORBIT, REFLECT, Ciclos e Analytics já existentes.
**Por quê:** Evita agravar o monolito AtivoView (~62KB) sem estrutura. NAV inline já existe como padrão de navegação no componente.
**Rejeitado:** Seção inline sem NAV — aumentaria o monolito sem ganho de estrutura.

### D03 — Relatórios são documentos em disco, não computação on-demand
**O que:** A aba consome .md gerados por relatorios.py e persistidos em disco via index.json.
**Por quê:** Infraestrutura já existe. Não há razão para recalcular o que já foi gerado e salvo.
**Rejeitado:** Resumos on-demand — redundância com backend existente, acoplamento desnecessário.

## Tensões abertas desta sessão

- [[BOARD/tensoes_abertas/B50_drawer_onboarding_estado_persistido]]
- [[BOARD/tensoes_abertas/B51_nav_relatorio_tune_exportavel]]
- [[BOARD/tensoes_abertas/B52_tp_stop_ativos_table]]

## Nota de reconstrução

Esta ata foi reconstruída em 2026-04-25 a partir de referências em B53 (nota: "SPEC_RELATORIO_TUNE_v1.0.md (B51) permanece independente — aba do ativo, não drawer") e do relato do CEO em sessão de 2026-04-25. O arquivo original não foi gravado em disco na data da sessão — falha operacional de Dalio corrigida via novo template que exige seção "Por quê" e "Rejeitado" por decisão.
