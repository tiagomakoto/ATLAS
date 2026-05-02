# PLAN — Step 3: Sub-fases visuais TAPE → ORBIT → FIRE → GATE

**Data:** 2026-05-02  
**Status:** APROVADO (Bloco 1)  
**Classificação:** Distribuída (2 arquivos, médio risco)

---

## BLOCO 1 — Impacto (Linguagem de negócio)

- O card do Step 3 passará a mostrar **4 sub-fases** em vez de 2: `TAPE → ORBIT → FIRE → GATE`
- Cada sub-fase terá uma **barra de progresso visual** idêntica à usada no Step 2 (barra horizontal azul com percentual)
- A ordem acompanhará exatamente o que o terminal exibe durante a execução
- O comportamento do sistema **não muda** — apenas a visibilidade e clareza do progresso
- O backend passará a emitir eventos WebSocket para TAPE, ORBIT e FIRE durante a execução do GATE backtest

---

## Contexto técnico

### Fluxo real do terminal no Step 3

1. `dc_gate_backtest()` emite `dc_module_start GATE`
2. Dentro de `gate_executar()`, chama `edge.executar()` que roda:
   - `[1/3] TAPE` — carrega dados históricos (**sem evento WS hoje**)
   - `[2/3] ORBIT` — classifica regimes (**sem evento WS hoje**)
   - `[3/3] FIRE` — itera pregões com barra tqdm (**sem evento WS hoje**)
3. Depois, GATE avalia os 8 critérios
4. Se GATE aprovar, `dc_fire_diagnostico()` roda separadamente (já emite evento WS FIRE)

### Problema

TAPE, ORBIT e FIRE (backtest) rodam dentro de `edge._executar_backtest()` sem emitir eventos WebSocket. O frontend só vê GATE e FIRE (diagnóstico).

### Padrão visual do Step 2 (referência)

- Container: `marginTop: 8, marginLeft: 20, borderLeft: "2px solid var(--atlas-border)", paddingLeft: 12`
- Label: `fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)"`
- Barra: `width: "100%", height: 6, background: "var(--atlas-border)", borderRadius: 4, overflow: "hidden"`
- Fill: `background: "var(--atlas-blue)"`, width proporcional ao progresso
- Status text: blue=running, green=done, secondary=idle

### Nota sobre progresso granular

TAPE, ORBIT e FIRE (backtest) não emitem progresso granular via WebSocket hoje. A barra mostrará 0% → 100% (binário). Para GATE, a barra pode usar `gateCriteriosProgresso.length / 8` como progresso granular. Se no futuro quiser progresso granular para FIRE (pregões processados), será necessário adicionar emissão de eventos `dc_module_progress` no loop tqdm de `edge._executar_backtest` — mas isso fica fora do escopo atual.

---

## BLOCO 2 — Tarefas (Técnico)

### TAREFA 1

**Arquivo:** `delta_chaos/edge.py`  
**Ação:** modificar  
**Escopo:** `_executar_backtest()` (linhas 387-516)  
**Detalhe:** Adicionar chamadas `emit_event()` para as 3 sub-fases internas do backtest:

- Antes de `[1/3] TAPE` (linha ~414): `emit_event("TAPE", "start", ticker=self.ativos[0])`
- Após TAPE concluir com sucesso (após linha ~420): `emit_event("TAPE", "done", ticker=self.ativos[0])`
- Se TAPE vazio (linha ~418): `emit_event("TAPE", "error", ticker=self.ativos[0])`
- Antes de `[2/3] ORBIT` (linha ~427): `emit_event("ORBIT", "start", ticker=self.ativos[0])`
- Após ORBIT concluir (após linha ~434): `emit_event("ORBIT", "done", ticker=self.ativos[0])`
- Se ORBIT vazio (linha ~431): `emit_event("ORBIT", "error", ticker=self.ativos[0])`
- Antes de `[3/3] FIRE` (linha ~450): `emit_event("FIRE", "start", ticker=self.ativos[0])`
- Após loop FIRE concluir (após linha ~515): `emit_event("FIRE", "done", ticker=self.ativos[0])`

**Constraints:** Não alterar lógica de execução — apenas adicionar emissão de eventos. Preservar todas as prints existentes.  
**Depende de:** nenhuma

---

### TAREFA 2

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`  
**Ação:** modificar  
**Escopo:** Constante `STEP3_FASES` (linha 26-29)  
**Detalhe:** Expandir de `{GATE, FIRE}` para `{TAPE: "tape", ORBIT: "orbit", FIRE: "fire", GATE: "gate"}`. Manter GATE e FIRE com os valores existentes.  
**Constraints:** Não alterar `STEPS` array nem `DEFAULT_STEPS`.  
**Depende de:** nenhuma

---

### TAREFA 3

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`  
**Ação:** modificar  
**Escopo:** Handler WebSocket `dc_module_start` (linhas 725-783)  
**Detalhe:** Adicionar handlers para os novos módulos no Step 3:

- `if (modulo === "TAPE")` → `setStep3Fase(STEP3_FASES.TAPE)` + atualizar `step3SubFases.TAPE = "running"`
- `if (modulo === "ORBIT")` → `setStep3Fase(STEP3_FASES.ORBIT)` + atualizar `step3SubFases.ORBIT = "running"`
- `if (modulo === "FIRE")` → já existe (linha 780), mas hoje só seta `STEP3_FASES.FIRE` — manter + atualizar `step3SubFases.FIRE = "running"`
- `if (modulo === "GATE")` → já existe (linha 763) — manter + atualizar `step3SubFases.GATE = "running"`

Importante: quando `modulo === "GATE"` e `step3Fase` já está em FIRE, significa que o backtest interno terminou e o GATE está avaliando critérios. O handler existente já faz `setStep3Fase(STEP3_FASES.GATE)` — manter.

**Constraints:** Não alterar handlers de Step 1 (TAPE/ORBIT/REFLECT no step 1). Os novos handlers só devem atuar quando Step 3 está running.  
**Depende de:** TAREFA 2, TAREFA 5

---

### TAREFA 4

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`  
**Ação:** modificar  
**Escopo:** Handler WebSocket `dc_module_complete` (linhas 785-898)  
**Detalhe:** Adicionar handlers para TAPE e ORBIT completando dentro do Step 3:

- `if (modulo === "TAPE")` → atualizar `step3SubFases.TAPE = ok ? "done" : "error"`
- `if (modulo === "ORBIT")` → atualizar `step3SubFases.ORBIT = ok ? "done" : "error"`
- `if (modulo === "FIRE")` → já existe (linha 880) — manter lógica existente + atualizar `step3SubFases.FIRE`

Nota: TAPE e ORBIT completando durante o Step 3 **não** devem fechar o Step 3 (diferente do Step 1 onde TAPE+ORBIT+REFLECT completando fecha o step). Apenas atualizam a sub-fase visual.

**Constraints:** Não alterar handlers existentes de Step 1. Não fechar Step 3 quando TAPE/ORBIT completam.  
**Depende de:** TAREFA 2, TAREFA 5

---

### TAREFA 5

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`  
**Ação:** modificar  
**Escopo:** State `step3Fase` e novos states para progresso das sub-fases  
**Detalhe:** Adicionar state para rastrear status de cada sub-fase do Step 3:

```javascript
const [step3SubFases, setStep3SubFases] = useState({
  TAPE: "idle",
  ORBIT: "idle",
  FIRE: "idle",
  GATE: "idle",
});
```

- Inicializar com todas em `"idle"`
- Atualizar conforme eventos WebSocket chegam (integrar com TAREFA 3 e 4)
- Resetar para idle quando Step 3 inicia (no handler `dc_module_start GATE`)

**Constraints:** Manter `step3Fase` existente para compatibilidade — pode ser derivado de `step3SubFases`.  
**Depende de:** TAREFA 2

---

### TAREFA 6

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`  
**Ação:** modificar  
**Escopo:** Renderização do Step 3 (linhas 1430-1459)  
**Detalhe:** Substituir as 2 linhas de texto (GATE/FIRE) por 4 linhas com barra de progresso, seguindo o padrão visual do Step 2:

```
TAPE: [████████████████████░░░░░░░░] 75% — ✓ ok / ⟳ executando... / ○ aguardando
ORBIT: [████████░░░░░░░░░░░░░░░░░░░] 25% — ⟳ executando...
FIRE: [░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0% — ○ aguardando
GATE: [░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0% — ○ aguardando
```

Padrão visual (idêntico ao Step 2):

- Container: `marginTop: 8, marginLeft: 20, borderLeft: "2px solid var(--atlas-border)", paddingLeft: 12`
- Cada sub-fase: label + barra + status text
- Label: `fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)"`
- Barra: `width: "100%", height: 6, background: "var(--atlas-border)", borderRadius: 4, overflow: "hidden"`
- Fill: `background: "var(--atlas-blue)"`, width proporcional ao progresso
- Status text: mesma lógica de cores do Step 2 (blue=running, green=done, secondary=idle)

Progresso por sub-fase:

- **TAPE**: binário (0% → 100%) — sem progresso intermediário
- **ORBIT**: binário (0% → 100%) — sem progresso intermediário
- **FIRE**: binário (0% → 100%) — tqdm não emite progresso via WS
- **GATE**: granular — `gateCriteriosProgresso.length / 8` (já existe state)

**Constraints:** Manter toda a lógica de critérios GATE existente abaixo (linhas 1460+). Não alterar o bloco de critérios progressivos.  
**Depende de:** TAREFA 5

---

### TAREFA 7

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`  
**Ação:** modificar  
**Escopo:** `useMemo` `step3GateStatus` e `step3FireStatus` (linhas 491-510)  
**Detalhe:** Refatorar para usar `step3SubFases` como fonte de verdade. Os `useMemo` existentes podem ser simplificados para ler de `step3SubFases.GATE` e `step3SubFases.FIRE`. Adicionar `useMemo` para `step3TapeStatus` e `step3OrbitStatus` se necessário para o render.  
**Constraints:** Manter assinatura e retorno dos useMemo existentes para compatibilidade.  
**Depende de:** TAREFA 5

---

### TAREFA 8

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`  
**Ação:** modificar  
**Escopo:** Inicialização/hidratação do Step 3 (linhas 527-545)  
**Detalhe:** Quando o componente monta e Step 3 está `running`, inferir a sub-fase atual:

- Se `step3Data.status === "running"` e não há `step3Fase` salvo, inferir baseado nos dados disponíveis (gateResult, fireDiag)
- Se Step 3 está `done`, marcar todas as sub-fases como "done"

**Constraints:** Não alterar lógica de fallback para API existente.  
**Depende de:** TAREFA 5

---

### TAREFA 9

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`  
**Ação:** modificar  
**Escopo:** Botão "Iniciar step 3 (GATE + FIRE)" (linha 1424)  
**Detalhe:** Atualizar texto do botão de "Iniciar step 3 (GATE + FIRE)" para "Iniciar step 3 (TAPE → ORBIT → FIRE → GATE)"  
**Constraints:** Nenhum  
**Depende de:** nenhuma

---

### TAREFA 10

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`  
**Ação:** modificar  
**Escopo:** Header do markdown do Step 3 (linha 136)  
**Detalhe:** Atualizar texto do header de "Validação (GATE + FIRE)" para "Validação (TAPE → ORBIT → FIRE → GATE)"  
**Constraints:** Nenhum  
**Depende de:** nenhuma

---

## Ordem de execução

```
TAREFA 1 (edge.py — emitir eventos)
TAREFA 2 (STEP3_FASES)
TAREFA 5 (step3SubFases state)
TAREFA 3 (dc_module_start handler)
TAREFA 4 (dc_module_complete handler)
TAREFA 7 (useMemo refatoração)
TAREFA 8 (hidratação)
TAREFA 6 (renderização — barras de progresso)
TAREFA 9 (texto botão)
TAREFA 10 (texto header markdown)
```

## Validação de consistência

- [x] Todas as dependências estão resolvidas
- [x] Não há tarefas fora de ordem
- [x] Não existe risco de conflito entre tarefas (TAREFA 1 é arquivo diferente; TAREFA 2-10 são seções não contíguas do mesmo arquivo)
- [x] Nenhuma tarefa viola escopo ou constraints
- [x] O BUILD conseguiria executar sem fazer perguntas

## Arquivos afetados

| Arquivo | Tarefas | Tipo de mudança |
|---------|---------|----------------|
| `delta_chaos/edge.py` | TAREFA 1 | Adicionar 8 chamadas `emit_event()` |
| `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx` | TAREFA 2-10 | Expandir sub-fases, state, handlers, render |
