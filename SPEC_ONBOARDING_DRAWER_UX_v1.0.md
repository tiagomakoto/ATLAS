# SPEC — OnboardingDrawer: melhorias de UX/UI
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board
**Data:** 2026-04-14
**Versão:** 1.0
**Modo:** Cirúrgico — melhorias visuais em componente existente

---

## BLOCO 1 — Contexto do projeto

Sistema: ATLAS — frontend React
Camada: `atlas_ui/src/components/GestaoView/OnboardingDrawer.jsx`
Tecnologias relevantes: React, CSS variables do ATLAS (`--atlas-green`, `--atlas-blue`, `--atlas-border`, `--atlas-text-secondary`, etc.)
O componente já existe e funciona — esta spec cobre apenas melhorias visuais e correções de UX observadas em uso real.

---

## BLOCO 2 — Situação atual

O `OnboardingDrawer.jsx` exibe:

**Topo do drawer:** bloco com três linhas de texto resumindo os steps:
```
Step 1 • CONCLUÍDO
Step 2 • PENDENTE      ← número errado (deveria ser Step 2)
Step 2 • PENDENTE      ← número errado (deveria ser Step 3)
```
Bug: ambos os steps pendentes exibem "Step 2" — a lógica de numeração está incorreta.

**Cards abaixo:** três cards com ícone, label de status e descrição genérica:
- Card verde: "CONCLUÍDO / Concluído / [timestamp]"
- Card cinza: "PENDENTE / Aguardando início" (sem nome da etapa)
- Card cinza: "PENDENTE / Aguardando início" (sem nome da etapa, idêntico ao anterior)

**Problemas identificados em uso real:**
1. Bug de numeração nos steps do resumo do topo
2. Resumo do topo é redundante com os cards — mesma informação duas vezes
3. Cards não mostram o nome da etapa (`backtest_dados`, `tune`, `backtest_gate`)
4. Steps pendentes são visualmente idênticos — não indica qual é o próximo
5. Step concluído não mostra duração — só timestamp de conclusão
6. Card do TUNE quando pendente não antecipa o que vai acontecer

---

## BLOCO 3 — Comportamento desejado

### 3.1 — Remover o bloco de resumo do topo

Remover completamente o bloco com as três linhas de texto ("Step 1 • CONCLUÍDO", etc.) que aparece acima dos cards. Os cards já contêm essa informação — o resumo é redundante e tem bug de numeração.

### 3.2 — Nome da etapa em cada card

Cada card exibe o nome técnico da etapa logo abaixo do label de status:

```
● CONCLUÍDO          ← label de status (existente)
  backtest_dados     ← nome da etapa (NOVO — em fonte menor, cinza)
  Concluído 14/04/2026, 11:16:56 · duração: 4m32s
```

```
○ PENDENTE
  tune
  Aguardando início
```

```
○ PENDENTE
  backtest_gate
  Aguardando início
```

Nomes exatos das etapas:
- Step 1 → `backtest_dados`
- Step 2 → `tune`
- Step 3 → `backtest_gate`

### 3.3 — Destaque visual do próximo step

O step imediatamente seguinte ao último `done` recebe fundo azul sutil em vez de cinza:

- `idle` padrão → fundo `rgba(156,163,175,0.1)`, borda `var(--atlas-border)` (atual)
- `idle` próximo → fundo `rgba(59,130,246,0.08)`, borda `rgba(59,130,246,0.3)` (NOVO)
- `running` → fundo `rgba(59,130,246,0.15)`, borda `var(--atlas-blue)` (atual)
- `done` → fundo `rgba(34,197,94,0.1)`, borda `var(--atlas-green)` (atual)
- `error` → fundo `rgba(239,68,68,0.1)`, borda `var(--atlas-red)` (atual)

**Regra para identificar o "próximo step":** é o primeiro step com status `idle` após o último step com status `done`. Se nenhum step está `done`, o próximo é o step 1.

### 3.4 — Duração no card concluído

Quando um step está `done`, exibir duração calculada a partir de `iniciado_em` e `concluido_em`:

```
Concluído 14/04/2026, 11:16:56 · duração: 4m32s
```

Formato da duração:
- Menos de 60s → `Xs`
- Entre 1min e 59min → `Xm Ys`
- 1h ou mais → `Xh Ym`

Se `iniciado_em` não estiver disponível no estado local, omitir a duração (exibir só o timestamp).

### 3.5 — Descrição prévia no card TUNE quando pendente

Quando o step 2 (`tune`) está `idle` e é o próximo step, exibir texto descritivo:

```
○ PRÓXIMO
  tune
  Optuna 200 trials · estimativa 4–8h
```

Apenas para o step 2 — steps 1 e 3 mantêm "Aguardando início".

### 3.6 — Label do próximo step

Quando um step `idle` é o próximo a executar, seu label muda de "PENDENTE" para "PRÓXIMO":

```
○ PRÓXIMO   ← em vez de "PENDENTE"
  tune
  Optuna 200 trials · estimativa 4–8h
```

---

## BLOCO 4 — O que não deve ser tocado

- Lógica de conexão WebSocket (`useWebSocket`) — não modificar
- Parsing de eventos (`handleEvento`) — não modificar
- Lógica de cálculo de timing do TUNE (barra de progresso, tempo decorrido, estimativa) — não modificar
- Cards quando `running` — comportamento atual preservado integralmente
- Card de conclusão do onboarding (botões Confirmar OPERAR / Manter MONITORAR) — não modificar
- Watchdog alert — não modificar
- Posicionamento e dimensões do drawer — não modificar
- `GestaoView.jsx` — não modificar
- `useWebSocket.js` — não modificar

---

*Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*
*Spec v1.0 — 2026-04-14*
