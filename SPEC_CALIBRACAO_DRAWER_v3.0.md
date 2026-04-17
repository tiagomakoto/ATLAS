# SPEC — CalibraçãoDrawer: reformulação completa (v3.0)
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board
**Data:** 2026-04-17
**Versão:** 3.0 (substitui SPEC_ONBOARDING_DRAWER_v2.0 + SPEC_ONBOARDING_DRAWER_UX_v1.0)
**Modo:** Especificação — reformulação estrutural de componente existente
**Tensões cobertas:** B51, B53

---

## BLOCO 1 — Contexto do projeto

Sistema: ATLAS — frontend React + backend FastAPI
Camada: `atlas_ui/src/components/GestaoView/CalibraçãoDrawer.jsx`
Tecnologias relevantes: React, WebSocket via `useWebSocket.js`, FastAPI
Regra inviolável: não modificar `useWebSocket.js`

**Decisões de board que originam esta spec:**
- Drawer renomeado de "Onboarding" para "Calibração" — o fluxo cobre tanto ativo novo quanto re-calibração de ativo já operacional. O nome "Onboarding" implica ação única e está incorreto.
- Fluxo único invariante: backtest_dados → TUNE → GATE. Mesma sequência para qualquer contexto de uso.
- GATE e FIRE são camadas independentes. GATE é portão histórico (binário, 8 critérios). FIRE no contexto de calibração é painel de inteligência — não bloqueante.
- Estrutura de steps: 3 steps. FIRE sai do fluxo de calibração e vai para relatório exportável no step 3.
- Step 3 (GATE): exibe pass/fail granular por critério antes de FIRE disparar.
- FIRE só dispara após GATE pass. Relatório FIRE exportável em `.md` ao final.

---

## BLOCO 2 — Situação atual

**O que existe e funciona:**
- `GestaoView.jsx` — importa `OnboardingDrawer` de `./GestaoView/OnboardingDrawer` e renderiza quando `drawerOnboarding !== null`
- `useWebSocket.js` — hook existente, conecta em `ws://localhost:8000/ws/events`
- `atlas_backend/core/dc_runner.py` — emite `dc_module_start` e `dc_module_complete` por módulo
- `atlas_backend/core/terminal_stream.py` — emite `terminal_log` com mensagens dos subprocessos
- Endpoint `POST /delta-chaos/onboarding` — já chamado pelo `GestaoView.jsx`
- `OnboardingDrawer.jsx` — componente existente com steps funcionais e WebSocket operacional

**O que muda nesta spec:**
- Arquivo renomeado: `OnboardingDrawer.jsx` → `CalibraçãoDrawer.jsx`
- `GestaoView.jsx` atualiza o import para o novo nome
- Step 3 reformulado: GATE com diagnóstico granular + FIRE como relatório exportável
- Melhorias de UX dos itens 1–6 da SPEC_ONBOARDING_DRAWER_UX_v1.0 incorporadas
- Guard de dados recentes no step 1

---

## BLOCO 3 — Comportamento desejado

### 3.1 — Renomeação do componente

**Arquivo:** renomear `OnboardingDrawer.jsx` → `CalibraçãoDrawer.jsx`
**Import em GestaoView.jsx:** atualizar de `./GestaoView/OnboardingDrawer` para `./GestaoView/CalibraçãoDrawer`
**Título exibido no drawer:** "CALIBRAÇÃO — {TICKER}" em vez de "ONBOARDING — {TICKER}"

### 3.2 — Estrutura de steps

```javascript
const STEPS = [
  { id: "1_backtest_dados", label: "backtest_dados", modulo: "ORBIT" },
  { id: "2_tune",           label: "tune",           modulo: "TUNE"  },
  { id: "3_gate_fire",      label: "gate + fire",    modulo: "GATE"  },
];
```

### 3.3 — Layout geral

```
┌─────────────────────────────────────────────────┐
│ CALIBRAÇÃO — PETR4                          [×] │
├─────────────────────────────────────────────────┤
│ ● CONCLUÍDO   backtest_dados                    │
│   Concluído 14/04/2026, 11:16:56 · duração: 4m32s│
├─────────────────────────────────────────────────┤
│ ○ PRÓXIMO     tune                              │
│   Optuna 200 trials · estimativa 4–8h           │
├─────────────────────────────────────────────────┤
│ ○ PENDENTE    gate + fire                       │
│   Aguardando início                             │
└─────────────────────────────────────────────────┘
```

**Estados visuais por card:**
- `idle` padrão → fundo `rgba(156,163,175,0.1)`, borda `var(--atlas-border)`, label "PENDENTE"
- `idle` próximo → fundo `rgba(59,130,246,0.08)`, borda `rgba(59,130,246,0.3)`, label "PRÓXIMO"
- `running` → fundo `rgba(59,130,246,0.15)`, borda `var(--atlas-blue)`, label "EXECUTANDO"
- `done` → fundo `rgba(34,197,94,0.1)`, borda `var(--atlas-green)`, label "CONCLUÍDO"
- `error` → fundo `rgba(239,68,68,0.1)`, borda `var(--atlas-red)`, label "ERRO"

**Regra "próximo step":** primeiro step com status `idle` após o último `done`. Se nenhum `done`, o próximo é o step 1.

**Nome técnico da etapa:** exibido abaixo do label em fonte menor, `var(--atlas-text-secondary)`.

**Duração no card concluído:**
```
Concluído DD/MM/AAAA, HH:MM:SS · duração: Xm Ys
```
Formato duração: `Xs` (< 60s) | `Xm Ys` (1–59min) | `Xh Ym` (≥ 1h).
Se `iniciado_em` não disponível, omitir duração.

**Descrição prévia no step 2 quando `idle` próximo:**
```
tune
Optuna 200 trials · estimativa 4–8h
```
Apenas para o step 2. Steps 1 e 3 mantêm "Aguardando início".

**Remover bloco de resumo do topo:** o bloco de texto com "Step 1 • CONCLUÍDO / Step 2 • PENDENTE" deve ser removido — é redundante com os cards.

### 3.4 — Guard de dados recentes (step 1)

Antes de executar o step 1, verificar data do último COTAHIST processado para o ticker (campo disponível no master JSON).

Se dados processados há menos de 7 dias, exibir no card do step 1 quando `idle`:

```
⚠ Dados atualizados em DD/MM — deseja rodar mesmo assim?
[Pular step 1]   [Rodar mesmo assim]
```

[Pular step 1] marca step 1 como `done` com label "PULADO" e avança para step 2.
[Rodar mesmo assim] executa normalmente.

Se dados com mais de 7 dias, ou data indisponível, executar step 1 diretamente sem guard.

### 3.5 — Step 2 (TUNE) — comportamento preservado da v2.0

Manter integralmente o comportamento de progresso do TUNE da SPEC_ONBOARDING_DRAWER_v2.0:
- Barra de progresso de trials
- Melhor IR em tempo real
- Tempo decorrido e estimativa restante
- Watchdog visual após 5 minutos sem evento `terminal_log`

### 3.6 — Step 3 — GATE com diagnóstico granular, seguido de FIRE

O step 3 é composto de duas fases sequenciais dentro do mesmo card:

#### Fase A — GATE

Ao receber `dc_module_complete` com `modulo="GATE"`:

Exibir resultado de cada um dos 8 critérios individualmente:

```
┌─────────────────────────────────────────────────┐
│ ● GATE                                          │
│                                                 │
│ E1  Taxa de acerto          ✓  94.2%            │
│ E2  IR mínimo               ✓  +3.34            │
│ E3  N mínimo de trades      ✓  69               │
│ E4  Consistência anual      ✓  4/4 anos         │
│ E5  IR por regime           ✗  NEUTRO_BULL: -0.2│
│ E6  Drawdown máximo         ✓  -12%             │
│ E7  Consecutivos negativos  ✓  2                │
│ E8  Cobertura de regimes    ✓  5/6              │
│                                                 │
│  RESULTADO: ✓ OPERAR                           │
│  (ou)                                           │
│  RESULTADO: ✗ BLOQUEADO — falhou E5             │
└─────────────────────────────────────────────────┘
```

Se GATE bloqueado: exibir critérios que falharam em vermelho. Card encerra aqui — FIRE não dispara. Botão de exportação GATE disponível.

Se GATE passou: exibir "OPERAR" em verde e disparar automaticamente a Fase B.

Os dados dos 8 critérios devem vir do payload do evento `dc_module_complete` do GATE, ou de endpoint `GET /ativos/{ticker}/gate-resultado`.

#### Fase B — FIRE (somente após GATE pass)

Ao receber `dc_module_complete` com `modulo="FIRE"`:

Exibir painel de inteligência histórica por regime:

```
┌─────────────────────────────────────────────────┐
│ ● FIRE — Diagnóstico histórico                  │
│                                                 │
│ Regime          Trades  Acerto  IR     Worst    │
│ ALTA            24      95.8%   +4.1   -R$320   │
│ BAIXA           18      88.9%   +2.7   -R$480   │
│ NEUTRO_BULL      8      87.5%   +1.9   -R$210   │
│ NEUTRO_BEAR     12      91.7%   +2.2   -R$390   │
│ NEUTRO_LATERAL   7      85.7%   +1.4   -R$260   │
│                                                 │
│ Estratégia dominante por regime:                │
│ ALTA → Bear Call Spread                         │
│ BAIXA → Bull Put Spread                         │
│ NEUTRO_* → CSP                                  │
│                                                 │
│ Cobertura: 69/84 ciclos históricos com operação │
│ Stops por regime: BAIXA concentra 4/7 stops     │
│                                                 │
│ [Exportar relatório .md]                        │
└─────────────────────────────────────────────────┘
```

Campos por regime: trades históricos, taxa de acerto, IR isolado do regime, worst trade (P&L do pior stop), estratégia dominante.
Global: cobertura (ciclos com operação / total), distribuição de stops por regime.

### 3.7 — Relatório exportável (.md)

Botão [Exportar relatório .md] disponível ao final do step 3, independente de GATE pass ou fail.

**Se GATE bloqueado:** exporta apenas resultado GATE com critérios.
**Se GATE passou + FIRE concluído:** exporta relatório completo GATE + FIRE.

**Nome do arquivo:**
- GATE bloqueado: `GATE_{TICKER}_{CICLO}_{DATA}_BLOQUEADO.md`
- GATE + FIRE: `CALIBRACAO_{TICKER}_{CICLO}_{DATA}.md`

**Conteúdo do relatório completo:**

```markdown
# Relatório de Calibração — {TICKER} — {CICLO}
**Data:** {DATA}
**Gerado por:** ATLAS

---

## GATE — Resultado por critério
| Critério | Resultado | Valor |
|----------|-----------|-------|
| E1 Taxa de acerto        | ✓/✗ | {valor} |
| E2 IR mínimo             | ✓/✗ | {valor} |
| E3 N mínimo de trades    | ✓/✗ | {valor} |
| E4 Consistência anual    | ✓/✗ | {valor} |
| E5 IR por regime         | ✓/✗ | {valor} |
| E6 Drawdown máximo       | ✓/✗ | {valor} |
| E7 Consecutivos negativos| ✓/✗ | {valor} |
| E8 Cobertura de regimes  | ✓/✗ | {valor} |

**Resultado:** OPERAR / BLOQUEADO

---

## FIRE — Diagnóstico histórico por regime
| Regime | Trades | Acerto | IR | Worst trade |
|--------|--------|--------|----|-------------|
{TABELA_REGIMES}

**Estratégia dominante por regime:**
{ESTRATEGIAS}

**Cobertura:** {CICLOS_COM_OP}/{TOTAL_CICLOS} ciclos históricos com operação
**Distribuição de stops:** {STOPS_POR_REGIME}
```

### 3.8 — Conclusão do fluxo

Quando step 3 fase B (`done`), substituir cards por:

```
┌─────────────────────────────────────────────────┐
│ ✓ CALIBRAÇÃO CONCLUÍDA — {TICKER}               │
│                                                 │
│ {TICKER} aprovado pelo GATE.                    │
│ Confirmar entrada em OPERAR?                    │
│                                                 │
│ [Confirmar OPERAR]    [Manter MONITORAR]        │
└─────────────────────────────────────────────────┘
```

Se GATE bloqueado, exibir:

```
┌─────────────────────────────────────────────────┐
│ ✗ GATE BLOQUEADO — {TICKER}                     │
│                                                 │
│ {TICKER} não passou na validação do GATE.       │
│ Critério(s) reprovado(s): {LISTA_FALHAS}        │
│                                                 │
│ [Exportar relatório GATE]    [Fechar]           │
└─────────────────────────────────────────────────┘
```

---

## BLOCO 4 — Backend — novos endpoints necessários

### GET /ativos/{ticker}/gate-resultado
Retorna resultado dos 8 critérios GATE para o ticker, com valores individuais e status pass/fail por critério.

### GET /ativos/{ticker}/fire-diagnostico
Retorna diagnóstico histórico FIRE por regime: trades, acerto, IR isolado, worst trade, estratégia dominante, cobertura.

Ambos os endpoints são read-only — apenas leitura do master JSON e dados históricos. Não escrevem nada.

---

## BLOCO 5 — O que não deve ser tocado

- `useWebSocket.js` — apenas consumir, não modificar
- Lógica de WebSocket e parsing de eventos — preservar da v2.0
- Barra de progresso e métricas de timing do TUNE — preservar da v2.0
- Watchdog alert — preservar da v2.0
- Botões [Confirmar OPERAR] / [Manter MONITORAR] — preservar da v2.0
- `OrchestratorProgress.jsx` — não modificar
- CSS variables existentes — usar exclusivamente
- Posicionamento e dimensões do drawer — preservar da v2.0

---

## BLOCO 6 — Referência a specs anteriores

Esta spec substitui integralmente:
- `SPEC_ONBOARDING_DRAWER_v2.0.md` — estrutura de steps e WebSocket
- `SPEC_ONBOARDING_DRAWER_UX_v1.0.md` — melhorias visuais (itens 1–6 incorporados)

Spec complementar (não substituída):
- `SPEC_RELATORIO_TUNE_v1.0.md` — relatório de TUNE na aba do ativo (B51) — independente desta spec

---

*Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*
*Spec v3.0 — 2026-04-17*
*Substitui: SPEC_ONBOARDING_DRAWER_v2.0.md + SPEC_ONBOARDING_DRAWER_UX_v1.0.md*
*Tensões cobertas: B51 (parcial — relatório TUNE independente), B53*
