# SPEC — Pendências Consolidadas B53 / B54 / B55 / B56 / B57
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board
**Data:** 2026-04-29
**Modo:** Cirúrgico — correções sobre código existente
**Tensões cobertas:** B53, B54, B55, B56, B57

---

> Esta spec consolida cinco tensões abertas auditadas por SCAN em 2026-04-29.
> Cada tarefa é independente. O PLAN deve executá-las na ordem indicada —
> há dependências explicitadas por tensão.

---

## BLOCO 1 — Contexto do projeto

Sistema: **Delta Chaos + ATLAS**
Camadas afetadas:
- `delta_chaos/edge.py` — orquestrador Python (módulos REFLECT, emissão de eventos)
- `delta_chaos/tape.py` — master JSON dos ativos
- `atlas_backend/core/relatorios.py` — gerador de relatórios .md
- `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx` — frontend React
- `atlas_ui/src/components/GestaoView.jsx` — import do drawer

Tecnologias: Python 3.x, React, FastAPI, WebSocket.

---

---

## TAREFA 1 — B54: remover dupla emissão de eventos em edge.py

### Situação atual
`dc_runner.py` importa `delta_chaos.edge` como módulo direto e emite
`dc_module_start` / `dc_module_complete` para cada módulo via `emit_dc_event`.
Porém, as funções `rodar_backtest_dados()` e `rodar_orbit_update()` em
`delta_chaos/edge.py` **também** emitem `emit_dc_event` de ciclo de vida
para TAPE, ORBIT e REFLECT internamente — causando dupla emissão: o
frontend recebe cada evento duas vezes sem erro aparente.

**Arquivo:** `delta_chaos/edge.py`
**Funções:** `rodar_backtest_dados()` e `rodar_orbit_update()`

Dentro de `rodar_backtest_dados()`, as chamadas a remover são:
```python
emit_dc_event("dc_module_start", "ORBIT", "running", ticker=ticker)
emit_dc_event("dc_module_start", "TAPE", "running", ticker=ticker)
emit_dc_event("dc_module_complete", "TAPE", "ok", ticker=ticker, ...)
emit_dc_event("dc_module_complete", "ORBIT", "ok", ticker=ticker)
emit_dc_event("dc_module_complete", "ORBIT", "error", ...)
emit_dc_event("dc_module_start", "REFLECT", "running", ticker=ticker)
emit_dc_event("dc_module_complete", "REFLECT", "ok", ticker=ticker)
emit_dc_event("dc_module_complete", "REFLECT", "error", ...)
```

Mesma lógica em `rodar_orbit_update()`.

### Comportamento desejado
- `rodar_backtest_dados()` e `rodar_orbit_update()` em `edge.py` **não emitem**
  nenhum `emit_dc_event` de ciclo de vida.
- `emit_log()` pode ser mantido — é log de terminal, sem impacto no frontend.
- `dc_runner.py` continua sendo o único emissor de `dc_module_start` e
  `dc_module_complete`. Esta é a regra arquitetural canônica (vault B54).
- Exceção que **não deve ser removida**: `tune.py` pode emitir `dc_tune_progress`.

### O que não deve ser tocado
- `dc_runner.py` — nenhuma modificação.
- `atlas_backend/core/event_bus.py` — nenhuma modificação.
- `emit_log()` e `emit_error()` em `edge.py` — manter.
- Bloco `if __name__ == "__main__":` em `edge.py` — manter intacto.
- Qualquer lógica de negócio de `rodar_backtest_dados()` e `rodar_orbit_update()` — apenas remover as chamadas `emit_dc_event`.

---

---

## TAREFA 2 — B55 + B56: limpeza REFLECT em edge.py e tape.py

> **Executar após TAREFA 1.**
> B55 e B56 compartilham arquivos — agrupados em tarefa única para evitar conflito.

### Situação atual

**B55 — TODO ausente em `reflect_cycle_calcular()`:**
O estado `T` (Tail) é atribuído puramente por score numérico (bloco `else`
após threshold D). Não há TODO documentando que o critério discreto de
evento de cauda está pendente (aguarda B04).

**B56 — Três itens pendentes:**

(a) `reflect_sizing_calcular()` em `edge.py` atribui `"A": 1.0` sem comentário
de que o alpha de estado A está pendente de B01/B29.

(b) `reflect_sizing_calcular()` em `edge.py` atribui `"C": 0.5` sem TODO de
revisão vinculado ao PE-007 (condição: 50 ciclos C + B30 implementado).

(c) `tape.py` — funções `tape_ativo_carregar()` e `tape_ativo_inicializar()`
ainda leem e escrevem o campo `regimes_sizing`. A constante
`REGIMES_SIZING_PADRAO` ainda é carregada do config. O campo é letra morta
operacionalmente (sizing agora vem de `reflect_sizing_calcular()`) mas
ainda ocupa código e JSONs.

### Comportamento desejado

**B55 — `reflect_cycle_calcular()` em `edge.py`:**

Localizar o bloco de atribuição de estado:
```python
    else:
        reflect_state = "T"  # Tail
```
Substituir por:
```python
    else:
        # TODO B55-etapa2: critério discreto de evento de cauda pendente (aguarda B04).
        # T é atribuído puramente por score < threshold_D até B04 ser resolvido.
        reflect_state = "T"  # Tail
```

**B56(a) — `reflect_sizing_calcular()` em `edge.py`:**

Localizar:
```python
    _lookup = {
        "A": 1.0,   # alpha pendente B01/B29
```
Se o comentário `# alpha pendente B01/B29` já está presente — sem alteração.
Se ausente, adicionar o comentário conforme acima.

**B56(b) — `reflect_sizing_calcular()` em `edge.py`:**

Localizar:
```python
        "C": 0.5,   # PE-007 — provisório
```
Substituir por:
```python
        "C": 0.5,   # PE-007 — provisório. TODO B56: revisar após 50 ciclos C + B30 implementado.
```

**B56(c) — `tape.py` — remoção de `regimes_sizing` em três etapas atômicas:**

**Etapa 1:** Em `tape_ativo_carregar()`, remover `regimes_sizing` do dict `default_config`
e remover o bloco de migração que garante sub-regimes em `regimes_sizing`:
```python
# REMOVER este bloco inteiro:
        # Garante sub-regimes em regimes_sizing
        for regime, sizing in REGIMES_SIZING_PADRAO.items():
            if regime not in dados["regimes_sizing"]:
                dados["regimes_sizing"][regime] = sizing
```
E remover `"regimes_sizing": REGIMES_SIZING_PADRAO.copy()` do `default_config`.

**Etapa 2:** Em `tape_ativo_inicializar()`, remover `"regimes_sizing"` do dict `defaults`
e remover o bloco `elif campo == "regimes_sizing":` inteiro.

**Etapa 3:** Remover a linha:
```python
REGIMES_SIZING_PADRAO = carregar_config()["fire"]["regimes_sizing_padrao"]
```
do topo de `tape.py` (constante privativa), se e somente se não houver outra
referência a `REGIMES_SIZING_PADRAO` no arquivo após as remoções das etapas 1 e 2.
Verificar com grep antes de remover.

> **Atenção:** JSONs existentes dos ativos podem ainda conter o campo
> `regimes_sizing`. Isso é inerte — o campo será ignorado na próxima leitura.
> Não é necessário migrar os JSONs agora.

### O que não deve ser tocado
- Lógica de negócio de `reflect_cycle_calcular()` além dos comentários de TODO.
- Lookup completo de estados em `reflect_sizing_calcular()` — apenas adicionar comentários.
- `delta_chaos_config.json` — não modificar.
- Qualquer outro módulo além de `edge.py` e `tape.py`.
- `reflect_daily_history`, `reflect_cycle_history`, `reflect_state` nos JSONs — não tocar.

---

---

## TAREFA 3 — B57: adicionar 6 campos diagnóstico no gerador de relatório

> **Executar após TAREFAS 1 e 2** (campos 3 e 4 dependem de estados B55/B56
> presentes no JSON; campos 1, 2, 5, 6 são independentes e podem ser
> implementados sem essa dependência, mas a tarefa é entregue inteira).

### Situação atual
`atlas_backend/core/relatorios.py` — função `gerar_relatorio_tune()` e
`formatar_relatorio_markdown()` — não contêm os seguintes campos:

1. Distribuição temporal de stops (em qual período/ano ocorreram os stops)
2. Breakdown de P&L por ano (P&L médio por trade, por ano civil)
3. Estado REFLECT atual do ativo (`reflect_state` do master JSON)
4. Sizing final recomendado (`sizing_orbit × reflect_mult` para o regime dominante)
5. Reconciliação TUNE × GATE (diferença de P&L médio entre janela TUNE e janela GATE)
6. Frequência de regimes na janela de backtest (quantos ciclos por regime)

### Comportamento desejado

**Em `gerar_relatorio_tune()`:**

Adicionar extração dos seguintes campos a partir de `dados_ativo` (retorno de `get_ativo_raw(ticker)`):

**Campo 1 — distribuição temporal de stops:**
```python
# A partir de historico[] do ativo — trades com motivo_saida == "STOP"
# Agrupar por ano. Retornar dict {"2022": N, "2023": N, ...}
stops_por_ano = {}  # extrair de dados_ativo.get("historico", [])
```

**Campo 2 — breakdown P&L por ano:**
```python
# A partir de historico[] do ativo
# Para cada ano: média de pnl dos trades daquele ano + N trades
# Retornar lista [{"ano": 2022, "pnl_medio": X, "n_trades": N}, ...]
pnl_por_ano = []
```
Incluir N trades por ano junto com P&L — sem N, o CEO não tem contexto para interpretar.

**Campo 3 — estado REFLECT atual:**
```python
reflect_state_atual = dados_ativo.get("reflect_state", None)
```

**Campo 4 — sizing final recomendado:**
```python
# sizing_orbit vem do último ciclo em historico[]
# reflect_mult vem do lookup de reflect_state_atual:
# A=1.0, B=1.0, C=0.5, D=0.0, T=0.0
_reflect_mult_map = {"A": 1.0, "B": 1.0, "C": 0.5, "D": 0.0, "T": 0.0}
reflect_mult = _reflect_mult_map.get(reflect_state_atual, 1.0)
ultimo_ciclo = dados_ativo.get("historico", [{}])[-1]
sizing_orbit = float(ultimo_ciclo.get("sizing", 0.0))
sizing_final = round(sizing_orbit * reflect_mult, 4)
```

**Campo 5 — reconciliação TUNE × GATE:**
```python
# pnl_medio_tune: pnl médio da janela TUNE (já disponível como pnl_medio)
# pnl_medio_gate: pnl médio da janela GATE (de gate_stats["pnl_medio"])
# diferenca = pnl_medio_tune - pnl_medio_gate
# nota_obrigatoria: True se abs(diferenca) > 0.5 E sign(tune) != sign(gate)
# threshold 0.5 é provisório — registrar como PE no vault após calibração
```

**Campo 6 — frequência de regimes na janela:**
```python
# A partir de historico[] do ativo — contar ciclos por regime
# Retornar dict {"ALTA": N, "NEUTRO_BULL": N, ...}
freq_regimes = {}
```

**Em `formatar_relatorio_markdown()`:**

Adicionar seção após "Distribuição de saídas":

```markdown
## Distribuição temporal de stops
| Ano | Stops |
|-----|-------|
| 2022 | 3 |
| 2023 | 1 |
...

## P&L por ano
| Ano | P&L médio/trade | N trades |
|-----|-----------------|----------|
| 2022 | R$ -45,20 | 18 |
| 2023 | R$ +32,10 | 22 |
...

## Frequência de regimes (janela de backtest)
| Regime | Ciclos |
|--------|--------|
| ALTA | 28 |
...

## Estado REFLECT atual
- Estado: {reflect_state_atual}
- Sizing final recomendado: {sizing_final} (orbit {sizing_orbit} × reflect {reflect_mult})

## Reconciliação TUNE × GATE
- P&L médio TUNE: R$ {pnl_medio_tune}
- P&L médio GATE: R$ {pnl_medio_gate}
- Diferença: R$ {diferenca}
{nota_obrigatoria}
```

Nota obrigatória (campo 5): se `nota_obrigatoria == True`, adicionar após diferença:
```
> ⚠ Divergência significativa entre janelas TUNE e GATE. Revisar com board
> antes de aplicar parâmetros. Possível sobreajuste ou viés de janela.
```

### O que não deve ser tocado
- Seções já existentes em `formatar_relatorio_markdown()` — apenas adicionar, não remover.
- Função `exportar_relatorio_calibracao()` — não modificar.
- Função `gerar_relatorio()` (TUNE legado) — não modificar.
- `index.json` e estrutura de arquivamento — não modificar.
- Nenhum endpoint de API — esta tarefa é apenas em `relatorios.py`.

---

---

## TAREFA 4 — B53: dois itens residuais no CalibracaoDrawer

> **Independente das demais. Pode ser executada em paralelo.**

### Situação atual

**Item A — GestaoView.jsx:**
SCAN não conseguiu verificar se o import em `GestaoView.jsx` já foi atualizado
de `OnboardingDrawer` para `CalibracaoDrawer`. Necessário confirmar e corrigir
se ainda estiver apontando para o nome antigo.

**Arquivo:** `atlas_ui/src/components/GestaoView.jsx`
**O que verificar:** linha de import do drawer e qualquer referência ao string
`"OnboardingDrawer"` ou `"ONBOARDING"` no componente.

**Item B — aviso N<5 no FIRE:**
`CalibracaoDrawer.jsx` — no painel FIRE diagnóstico histórico por regime
(seção que itera `fireDiag.regimes`), regimes com menos de 5 trades exibem
IR e acerto sem nenhum aviso visual. Um regime com 2 trades não tem poder
estatístico para IR ser interpretado como sinal.

**Arquivo:** `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`
**Localização exata:** bloco que mapeia `fireDiag.regimes` e renderiza cada linha
(`fireDiag.regimes.map((r) => ...)`).

### Comportamento desejado

**Item A — GestaoView.jsx:**
Localizar qualquer ocorrência de `OnboardingDrawer` (import, prop, string, comentário).
Se encontrado: substituir por `CalibracaoDrawer`.
Se já estiver correto: sem alteração.

**Item B — aviso N<5:**
No map de `fireDiag.regimes`, para cada regime onde `r.trades < 5`,
adicionar badge ou texto de aviso inline:

```jsx
{r.trades < 5 && (
  <span style={{
    fontFamily: "monospace",
    fontSize: 8,
    color: "var(--atlas-amber)",
    marginLeft: 4
  }}>
    ⚠ N&lt;5
  </span>
)}
```

O aviso deve aparecer na mesma linha do regime, após o valor de IR.
Não deve ocultar nem substituir os valores — apenas sinalizar.

### O que não deve ser tocado
- `useWebSocket.js` — nenhuma modificação.
- Lógica de WebSocket, polling e watchdog em `CalibracaoDrawer.jsx` — preservar intactos.
- Estrutura dos cards de steps — não modificar.
- CSS variables — usar exclusivamente as existentes.
- Qualquer arquivo fora de `GestaoView.jsx` e `CalibracaoDrawer.jsx`.

---

---

## Ordem de execução recomendada

| Ordem | Tarefa | Arquivo(s) principal(is) | Dependência |
|-------|--------|--------------------------|-------------|
| 1 | B54 — remover dupla emissão | `delta_chaos/edge.py` | nenhuma |
| 2 | B55+B56 — TODOs e remoção `regimes_sizing` | `edge.py`, `tape.py` | após T1 |
| 3 | B57 — 6 campos diagnóstico | `atlas_backend/core/relatorios.py` | após T2 |
| 4 | B53 — import + aviso N<5 | `GestaoView.jsx`, `CalibracaoDrawer.jsx` | nenhuma |

Tarefas 1 e 4 são independentes entre si e podem ser executadas em paralelo.
Tarefa 3 deve ser executada após Tarefa 2 (campos 3 e 4 leem `reflect_state`
e `sizing` que dependem da limpeza de `regimes_sizing` estar feita).

---

## Definição de pronto

- [ ] **T1:** grep em `edge.py` por `emit_dc_event` dentro de `rodar_backtest_dados()` e `rodar_orbit_update()` retorna zero ocorrências de eventos de ciclo de vida.
- [ ] **T2-B55:** comentário TODO de critério de cauda presente após `reflect_state = "T"`.
- [ ] **T2-B56a:** comentário `# B01/B29` presente na linha `"A": 1.0` do lookup.
- [ ] **T2-B56b:** comentário `TODO B56` presente na linha `"C": 0.5` do lookup.
- [ ] **T2-B56c:** grep por `regimes_sizing` em `tape.py` retorna zero ocorrências. `REGIMES_SIZING_PADRAO` removido ou ausente se sem outros usos.
- [ ] **T3:** `formatar_relatorio_markdown()` contém seções "Distribuição temporal de stops", "P&L por ano", "Frequência de regimes", "Estado REFLECT atual", "Reconciliação TUNE × GATE". Campo 5 emite nota obrigatória quando `nota_obrigatoria == True`.
- [ ] **T4-A:** grep por `OnboardingDrawer` em `GestaoView.jsx` retorna zero ocorrências.
- [ ] **T4-B:** regimes com `r.trades < 5` exibem badge `⚠ N<5` em amber no painel FIRE.

---

*Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*
*Spec consolidada — 2026-04-29*
*Tensões cobertas: B53, B54, B55, B56, B57*
*Auditoria SCAN base: 2026-04-29*
