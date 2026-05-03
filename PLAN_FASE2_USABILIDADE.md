# Fase #2 — Usabilidade (CalibracaoDrawer)

**Data:** 2026-05-03
**Status:** AGUARDANDO APROVAÇÃO
**Escopo:** Apenas `CalibracaoDrawer.jsx`
**Prioridade:** Acessibilidade + Performance equilibradas
**Duração estimada:** 2-3 dias

---

## BLOCO 1 — PARA APROVAÇÃO (LINGUAGEM DE NEGÓCIO)

### O que muda para o usuário

- **Nenhuma mudança visual.** O layout, cores, textos e animações permanecem idênticos.
- Leitores de tela (NVDA, VoiceOver) passarão a anunciar o progresso de cada sub-fase do Step 3 (TAPE, ORBIT, FIRE, GATE) com percentual e status textual — hoje as barras são mudas para tecnologia assistiva.
- O botão de fechar o drawer (×) passará a ter um nome acessível ("Fechar calibração").
- O drawer passará a ser identificado como diálogo modal para leitores de tela.

### O que muda no comportamento do sistema

- **Zero mudança funcional.** Nenhum handler, nenhum evento WS, nenhuma API é alterada.
- O componente interno que renderiza cada barra de progresso será extraído para um componente `SubFaseProgressBar` com `React.memo`. Isso reduz re-renders quando apenas uma sub-fase muda (ex: TAPE muda para "done" mas ORBIT/FIRE/GATE continuam "idle" — só a barra de TAPE re-renderiza).
- Os 4 `useMemo` decorativos (linhas 514-517) serão removidos — cada um apenas extrai uma propriedade de `step3SubFases` com dependência no objeto inteiro, sem benefício de memoização. Acesso direto à propriedade é mais simples e igualmente eficiente.

### Efeitos visíveis ou perceptíveis

- Nenhum efeito visual perceptível.
- Usuários de leitor de tela perceberão anúncios de progresso onde antes havia silêncio.
- Em React DevTools Profiler, haverá menos re-renders do componente principal durante backtest.

### Impacto em interfaces/contratos

- Nenhum. O componente `SubFaseProgressBar` é interno (não exportado). Nenhuma prop de `CalibracaoDrawer` muda. Nenhum evento WS é adicionado ou modificado.

---

## BLOCO 2 — PARA O BUILD (TÉCNICO)

### Classificação da mudança

**Distribuída** (múltiplos pontos no mesmo arquivo, médio risco)

### Arquivo único

`C:\Users\tiago\OneDrive\Documentos\ATLAS\atlas_ui\src\components\GestaoView\CalibracaoDrawer.jsx`

### Indentação

2 espaços. Preservar exatamente.

---

### TAREFA 1

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`
**Ação:** adicionar
**Escopo:** antes da linha 411 (antes de `function TuneRegimeProgressPanel`)
**Detalhe:** Criar componente `SubFaseProgressBar` com `React.memo`:

```jsx
const SubFaseProgressBar = React.memo(function SubFaseProgressBar({ modulo, status, percent, errorText, barColor }) {
  const statusLabel = status === "running" ? "⟳ executando..." : status === "done" ? "✓ ok" : status === "error" ? "✗ erro" : "○ aguardando";
  const textColor = status === "running" ? barColor : status === "done" ? "var(--atlas-green)" : status === "error" ? "var(--atlas-red)" : "var(--atlas-text-secondary)";
  const fontWeight = status === "running" ? "bold" : "normal";
  const numericPercent = status === "done" ? 100 : status === "running" ? (typeof percent === "number" ? percent : 50) : 0;

  return (
    <div
      style={{ marginBottom: 6 }}
      title={status === "error" ? (errorText || "Erro") : ""}
      role="progressbar"
      aria-label={`Progresso ${modulo}: ${statusLabel}`}
      aria-valuenow={numericPercent}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
        <span style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)" }}>{modulo}:</span>
        <span style={{ fontFamily: "monospace", fontSize: 9, color: textColor, fontWeight }}>
          {statusLabel}
        </span>
      </div>
      <div style={{ width: "100%", height: 6, background: "var(--atlas-border)", borderRadius: 4, overflow: "hidden" }}>
        <div style={{ width: `${numericPercent}%`, height: "100%", background: barColor, transition: "width 0.3s" }} />
      </div>
    </div>
  );
});
```

**Constraints:**
- Não alterar nenhuma outra parte do arquivo
- O componente deve ser definido FORA de `CalibracaoDrawer` (antes da linha 465) para que `React.memo` funcione corretamente
- `barColor` é prop explícito (não derivado internamente) para permitir que FIRE use `#a855f7` e os demais usem `var(--atlas-blue)`
- `percent` é prop numérico (0-100) para suportar futuro progresso granular da Fase #3 — valor padrão será 50 para running (comportamento binário atual)

**Depende de:** nenhuma

---

### TAREFA 2

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`
**Ação:** modificar
**Escopo:** linhas 1473-1542 (bloco de renderização das 4 sub-fases dentro de `renderStepCard`)
**Detalhe:** Substituir as 4 barras inline (TAPE, ORBIT, FIRE, GATE) por chamadas ao componente `SubFaseProgressBar`. O bloco atual (linhas 1473-1542) deve ser substituído por:

```jsx
<div style={{ marginTop: 8, marginLeft: 20, borderLeft: "2px solid var(--atlas-border)", paddingLeft: 12 }}>
  <SubFaseProgressBar modulo="TAPE" status={step3SubFases.TAPE} percent={50} errorText={step3SubFasesErrors.TAPE} barColor="var(--atlas-blue)" />
  <SubFaseProgressBar modulo="ORBIT" status={step3SubFases.ORBIT} percent={50} errorText={step3SubFasesErrors.ORBIT} barColor="var(--atlas-blue)" />
  <SubFaseProgressBar modulo="FIRE" status={step3SubFases.FIRE} percent={50} errorText={step3SubFasesErrors.FIRE} barColor="#a855f7" />
  <SubFaseProgressBar modulo="GATE" status={step3SubFases.GATE} percent={Math.round((gateCriteriosProgresso.length / 8) * 100)} errorText={step3SubFasesErrors.GATE} barColor="var(--atlas-blue)" />
</div>
```

**Constraints:**
- Preservar o container `<div style={{ marginTop: 8, marginLeft: 20, borderLeft: "2px solid var(--atlas-border)", paddingLeft: 12 }}>` exatamente
- Preservar a condicional `{status === "running" && (` que envolve o bloco
- FIRE usa `barColor="#a855f7"` (roxo) — os demais usam `barColor="var(--atlas-blue)"`
- GATE usa `percent={Math.round((gateCriteriosProgresso.length / 8) * 100)}` — progresso granular existente
- TAPE/ORBIT/FIRE usam `percent={50}` — progresso binário (0% → 50% → 100%), preparado para Fase #3
- Acesso direto a `step3SubFases.TAPE` etc. (sem os useMemo intermediários — ver TAREFA 3)

**Depende de:** TAREFA 1

---

### TAREFA 3

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`
**Ação:** remover
**Escopo:** linhas 514-517 (4 useMemo decorativos)
**Detalhe:** Remover as 4 linhas:

```jsx
const step3TapeStatus = useMemo(() => step3SubFases.TAPE, [step3SubFases]);
const step3OrbitStatus = useMemo(() => step3SubFases.ORBIT, [step3SubFases]);
const step3FireStatus = useMemo(() => step3SubFases.FIRE, [step3SubFases]);
const step3GateStatus = useMemo(() => step3SubFases.GATE, [step3SubFases]);
```

Após a remoção, buscar e substituir todas as referências a `step3TapeStatus`, `step3OrbitStatus`, `step3FireStatus`, `step3GateStatus` no arquivo por `step3SubFases.TAPE`, `step3SubFases.ORBIT`, `step3SubFases.FIRE`, `step3SubFases.GATE` respectivamente.

**Constraints:**
- Não alterar o `useMemo` de `proximoStep` (linha 503-512) — esse é legítimo
- Verificar que não há outras referências além das substituições esperadas
- A TAREFA 2 já usa acesso direto (`step3SubFases.TAPE`), mas pode haver referências em outros pontos do arquivo (hidratação, handlers, etc.)

**Depende de:** TAREFA 2 (para evitar conflito de substituição)

---

### TAREFA 4

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`
**Ação:** modificar
**Escopo:** linha 1 (import React)
**Detalhe:** Adicionar `useCallback` ao import de React se ainda não estiver presente. Verificar se é necessário — análise mostra que `useCallback` nos handlers **não traz benefício real** porque:
1. O hook `useWebSocket` usa `useRef` internamente (linha 4-5 de useWebSocket.js), logo a referência do callback não importa
2. Todos os handlers são usados apenas como `onClick` em `<button>` nativo — nenhum é passado como prop a componente filho memoizado

**Decisão:** NÃO adicionar `useCallback`. Justificativa documentada no plano. Se o CEO quiser `useCallback` por consistência futura, pode ser adicionado como tarefa opcional.

**Constraints:**
- Não adicionar `useCallback` sem necessidade real

**Depende de:** nenhuma (tarefa de decisão — nenhuma mudança de código)

---

### TAREFA 5

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`
**Ação:** modificar
**Escopo:** linha 1657-1662 (botão de fechar do drawer)
**Detalhe:** Adicionar `aria-label="Fechar calibração"` ao botão de fechar:

```jsx
<button
  onClick={onClose}
  aria-label="Fechar calibração"
  style={{ background: "transparent", border: "none", fontSize: 16, color: "var(--atlas-text-secondary)", cursor: "pointer" }}
>
  ×
</button>
```

**Constraints:**
- Não alterar o estilo ou comportamento do botão
- Não adicionar texto visível — apenas `aria-label`

**Depende de:** nenhuma

---

### TAREFA 6

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`
**Ação:** modificar
**Escopo:** linha 1637-1650 (container principal do drawer)
**Detalhe:** Adicionar `role="dialog"` e `aria-modal="true"` e `aria-label="Calibração"` ao `<div>` principal do drawer:

```jsx
<div
  role="dialog"
  aria-modal="true"
  aria-label="Calibração"
  style={{
    position: "fixed",
    top: 0,
    right: 0,
    width: "400px",
    height: "100%",
    background: "var(--atlas-surface)",
    borderLeft: "1px solid var(--atlas-border)",
    zIndex: 1000,
    padding: 16,
    overflowY: "auto",
    boxShadow: "-5px 0 15px rgba(0,0,0,0.1)",
  }}
>
```

**Constraints:**
- Não alterar nenhum estilo existente
- Não adicionar focus trap (fora do escopo — o drawer é o único operador, não há risco de confusão modal)

**Depende de:** nenhuma

---

### TAREFA 7

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`
**Ação:** modificar
**Escopo:** linha 1 (import)
**Detalhe:** Adicionar `memo` ao import de React, caso `React.memo` seja usado via import nomeado em vez de `React.memo`:

Verificar se o arquivo usa `import React, { ... } from "react"` (sim, linha 1). O componente `SubFaseProgressBar` da TAREFA 1 usa `React.memo(function ...)` — isso funciona com o import atual. Nenhuma mudança necessária no import.

**Constraints:**
- Não alterar o import se `React.memo` já funciona com o import atual

**Depende de:** TAREFA 1 (verificação pós-implementação)

---

### TAREFA 8 (TESTE)

**Arquivo:** `atlas_ui/src/components/GestaoView/__tests__/CalibracaoDrawer.usability.test.jsx`
**Ação:** criar
**Escopo:** testes de acessibilidade e performance do SubFaseProgressBar
**Detalhe:** Criar arquivo de teste com:

1. **Renderização do SubFaseProgressBar** — verificar que o componente renderiza com props corretos
2. **Acessibilidade** — verificar presença de `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, `aria-label`
3. **Status idle** — `aria-valuenow=0`, label contém "aguardando"
4. **Status running** — `aria-valuenow=50` (padrão binário), label contém "executando"
5. **Status done** — `aria-valuenow=100`, label contém "ok"
6. **Status error** — `title` contém texto de erro, label contém "erro"
7. **React.memo** — renderizar com mesmas props duas vezes, verificar que só renderiza uma vez
8. **Botão fechar** — verificar `aria-label="Fechar calibração"`
9. **Dialog** — verificar `role="dialog"` e `aria-modal="true"` no container

**Constraints:**
- Não alterar código de produção
- Usar `@testing-library/react` (verificar se já é dependência do projeto)
- Se `@testing-library/react` não estiver disponível, criar testes como comentários documentais estruturados

**Depende de:** TAREFAS 1, 2, 5, 6

---

## ORDEM DE EXECUÇÃO

```
TAREFA 1 (SubFaseProgressBar) ──→ TAREFA 2 (substituir inline) ──→ TAREFA 3 (remover useMemo)
                                                                    │
TAREFA 5 (aria-label botão) ──────────────────────────────────────┤
TAREFA 6 (role=dialog) ───────────────────────────────────────────┤
                                                                    ↓
                                                              TAREFA 8 (testes)
```

TAREFAS 1, 5 e 6 podem ser executadas em paralelo (não têm dependência entre si).
TAREFA 2 depende de TAREFA 1.
TAREFA 3 depende de TAREFA 2.
TAREFA 7 é verificação (sem mudança de código).
TAREFA 8 depende de 1, 2, 5, 6.

---

## VALIDAÇÃO FINAL

- [ ] Visual idêntico ao anterior (comparar screenshot antes/depois)
- [ ] `role="progressbar"` presente nas 4 barras (inspecionar DOM)
- [ ] `aria-valuenow` reflete percentual correto para cada status
- [ ] `aria-label` contém nome do módulo e status textual
- [ ] Botão × tem `aria-label="Fechar calibração"`
- [ ] Container tem `role="dialog"` e `aria-modal="true"`
- [ ] `useMemo` decorativos removidos — acesso direto a `step3SubFases.*`
- [ ] React DevTools: SubFaseProgressBar não re-renderiza quando props não mudam
- [ ] Nenhum handler WS alterado
- [ ] Nenhum evento WS adicionado ou modificado
- [ ] `py_compile` em edge.py (verificar que não foi alterado) — exit 0
