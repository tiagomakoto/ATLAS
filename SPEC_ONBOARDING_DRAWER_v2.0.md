# SPEC — OnboardingDrawer: componente real com progresso via WebSocket
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board
**Data:** 2026-04-13
**Versão:** 2.0 (substitui SPEC_ONBOARDING_DRAWER_v1.0)
**Modo:** Especificação — componente novo com infraestrutura existente

---

## BLOCO 1 — Contexto do projeto

Sistema: ATLAS — frontend React + backend FastAPI
Camada: Frontend (`atlas_ui/src/components/GestaoView/OnboardingDrawer.jsx`) — arquivo importado pelo GestaoView mas **que não existe ainda**
Tecnologias relevantes: React, WebSocket via `useWebSocket.js`, eventos `terminal_log` no formato `{type: "terminal_log", data: {message, level}}`
Regra inviolável: não modificar `useWebSocket.js`

---

## BLOCO 2 — Situação atual

**O que existe e funciona:**

- `GestaoView.jsx` — importa `OnboardingDrawer` de `./GestaoView/OnboardingDrawer` e renderiza `<OnboardingDrawer ticker={drawerOnboarding} onClose={() => setDrawerOnboarding(null)} />` quando `drawerOnboarding !== null`
- `GestaoView.jsx` — define `drawerOnboarding` como state; seta o valor após `handleOnboarding()` bem-sucedido com o ticker
- `useWebSocket.js` — hook existente, conecta em `ws://localhost:8000/ws/events`, chama `onMessage(data)` a cada evento recebido
- `atlas_backend/core/terminal_stream.py` — `emit_log(msg, level)` emite evento `{type: "terminal_log", data: {message: msg, level: level}}` via WebSocket
- `tune.py` — emite via `emit_log` a cada trial: `"TUNE [VALE3] trial 80/200 best_ir=+1.2340 sem_melhoria=3"`
- `dc_runner.py` — emite `dc_module_start` e `dc_module_complete` via `emit_dc_event` para cada módulo (ORBIT, GATE, etc.)
- `OrchestratorProgress.jsx` — componente existente com segmentos coloridos (cinza/azul/verde) e lógica de estado visual — **modelo de UX a seguir**
- `atlas_backend/core/dc_runner.py` — `dc_onboarding_iniciar()` e `dc_onboarding_retomar()` já implementados
- Endpoint `POST /delta-chaos/onboarding` — já chamado pelo `GestaoView.jsx`

**O que não existe:**

- `atlas_ui/src/components/GestaoView/OnboardingDrawer.jsx` — **arquivo ausente**, causa erro de import silencioso
- Nenhum componente ouve eventos WebSocket de TUNE durante onboarding
- Nenhum componente renderiza progresso dos três steps

---

## BLOCO 3 — Comportamento desejado

### 3.1 — Criar arquivo OnboardingDrawer.jsx

**Caminho:** `atlas_ui/src/components/GestaoView/OnboardingDrawer.jsx`

O componente recebe `{ ticker, onClose }` como props.

### 3.2 — Layout visual

Seguir o padrão visual de `OrchestratorProgress.jsx`: segmentos coloridos, monospace, fundo `var(--atlas-surface)`, bordas `var(--atlas-border)`.

```
┌─────────────────────────────────────────────────┐  ← painel lateral fixo,
│ ONBOARDING — VALE3                          [×] │     não modal
├─────────────────────────────────────────────────┤
│ ● STEP 1  backtest_dados              ✓ DONE    │  ← luz verde
│   Concluído 2026-04-13 22:01                    │
├─────────────────────────────────────────────────┤
│ ⟳ STEP 2  tune                      EXECUTANDO  │  ← luz azul piscando
│   ████████████░░░░░░  80 / 200 trials           │  ← barra progresso
│   Melhor IR: +1.2340                            │
│   Tempo médio/trial: 1.8s                       │
│   Decorrido: 2m 24s                             │
│   Estimativa restante: ~4min                    │
├─────────────────────────────────────────────────┤
│ ○ STEP 3  backtest_gate              PENDENTE   │  ← luz cinza
└─────────────────────────────────────────────────┘
```

### 3.3 — Estado dos steps

Cada step tem um estado local no componente:

```javascript
const STEPS = [
  { id: "1_backtest_dados", label: "backtest_dados", modulo: "ORBIT" },
  { id: "2_tune",           label: "tune",           modulo: "TUNE"  },
  { id: "3_backtest_gate",  label: "backtest_gate",  modulo: "GATE"  },
];
```

Estados possíveis por step: `"idle"` | `"running"` | `"done"` | `"error"`

Estado inicial ao montar: step 1 `running`, steps 2 e 3 `idle`.

**Indicadores visuais por estado:**
- `idle` → ○ cinza, label "PENDENTE"
- `running` → ● azul animado (pulse), label "EXECUTANDO"
- `done` → ● verde, label "DONE", exibe timestamp de conclusão
- `error` → ● vermelho, label "ERRO", exibe mensagem de erro

### 3.4 — Conexão WebSocket

O componente usa `useWebSocket` para receber eventos:

```javascript
import useWebSocket from "../../hooks/useWebSocket";

useWebSocket("ws://localhost:8000/ws/events", (evento) => {
  // dois tipos de evento relevantes:
  // 1. {type: "terminal_log", data: {message, level}}
  // 2. {type: "dc_module_start"|"dc_module_complete", data: {modulo, status, ...}}
  handleEvento(evento);
});
```

### 3.5 — Parsing de eventos

**Evento `dc_module_start`:**
```javascript
if (evento.type === "dc_module_start") {
  const modulo = evento.data.modulo; // "ORBIT", "TUNE", "GATE"
  // mapear modulo → step e setar status "running"
}
```

**Evento `dc_module_complete`:**
```javascript
if (evento.type === "dc_module_complete") {
  const modulo = evento.data.modulo;
  const status = evento.data.status; // "ok" ou "error"
  // mapear modulo → step
  // "ok" → setar "done" + timestamp
  // "error" → setar "error" + mensagem
  // se step 1 done → step 2 passa a aguardar dc_module_start de TUNE
  // se step 2 done → step 3 passa a aguardar dc_module_start de GATE
}
```

**Evento `terminal_log` com mensagem de trial TUNE:**
```javascript
if (evento.type === "terminal_log") {
  const msg = evento.data.message;
  // Padrão: "TUNE [VALE3] trial 80/200 best_ir=+1.2340 sem_melhoria=3"
  const match = msg.match(/TUNE \[[\w]+\] trial (\d+)\/(\d+) best_ir=([+-]?\d+\.\d+)/);
  if (match) {
    setTrialAtual(parseInt(match[1]));
    setTrialTotal(parseInt(match[2]));
    setBestIr(parseFloat(match[3]));
    setUltimoEventoEm(Date.now()); // para cálculo de tempo médio
  }
}
```

### 3.6 — Métricas de timing (step 2)

Calcular e exibir no card do step 2 quando `status === "running"`:

```javascript
// Tempo decorrido desde início do step 2
const decorrido = Math.floor((Date.now() - step2IniciadoEm) / 1000); // segundos

// Tempo médio por trial
const tempoMedio = trialAtual > 0 ? decorrido / trialAtual : 0;

// Estimativa restante
const restantes = trialTotal - trialAtual;
const estimativa = Math.floor(tempoMedio * restantes);
```

Exibir em formato legível: `"2m 24s"` para segundos, `"~4min"` para estimativa.

### 3.7 — Watchdog visual

Se `status === "running"` no step 2 e não recebe nenhum evento `terminal_log` de trial por mais de 5 minutos, exibe banner âmbar abaixo do card:

```
⚠ Sem sinal há 6min — processo pode ter sido interrompido
```

Não altera estado — apenas alerta. Implementar com `setInterval` local que verifica `Date.now() - ultimoEventoEm`.

### 3.8 — Posicionamento do drawer

Painel lateral fixo à direita da tela, sobrepõe o conteúdo sem ser modal:

```css
position: fixed;
top: 0;
right: 0;
width: 380px;
height: 100vh;
z-index: 1000;
background: var(--atlas-bg);
border-left: 1px solid var(--atlas-border);
overflow-y: auto;
```

Botão [×] fecha o drawer (chama `onClose()`). O processo continua rodando em background — fechar o drawer não cancela o onboarding.

### 3.9 — Conclusão do onboarding

Quando step 3 muda para `done`, substituir os cards dos steps por:

```
┌─────────────────────────────────────────────────┐
│ ✓ ONBOARDING CONCLUÍDO — VALE3                  │
│                                                 │
│ VALE3 aprovado pelo GATE.                       │
│ Confirmar entrada em OPERAR?                    │
│                                                 │
│ [Confirmar OPERAR]    [Manter MONITORAR]        │
└─────────────────────────────────────────────────┘
```

Botão [Confirmar OPERAR] chama `POST /ativos/{ticker}/status` com `{status: "OPERAR"}`.
Botão [Manter MONITORAR] chama `onClose()` sem alteração de status.

---

## BLOCO 4 — O que não deve ser tocado

- `useWebSocket.js` — apenas consumir, não modificar
- `GestaoView.jsx` — não modificar; o componente já importa e renderiza `OnboardingDrawer` corretamente
- `OrchestratorProgress.jsx` — não modificar; usar como referência visual apenas
- `atlas_backend/core/dc_runner.py` — não modificar; eventos já estão sendo emitidos
- `atlas_backend/core/terminal_stream.py` — não modificar
- `delta_chaos/tune.py` — não modificar nesta tarefa
- CSS variables existentes (`--atlas-surface`, `--atlas-border`, `--atlas-blue`, `--atlas-green`, `--atlas-red`, `--atlas-amber`, `--atlas-text-primary`, `--atlas-text-secondary`) — usar exclusivamente

---

## Observação crítica

O canal WebSocket já funciona. Os eventos já estão sendo emitidos pelo backend. O único arquivo que falta é `GestaoView/OnboardingDrawer.jsx`. Esta é uma tarefa de frontend puro — zero mudanças no backend ou no Delta Chaos.

---

*Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*
*Spec v2.0 — 2026-04-13*
*Substitui: SPEC_ONBOARDING_DRAWER_v1.0.md*
