# SPEC — Aba Gestão (renomeação de Manutenção + nova estrutura)
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board  
**Data:** 2026-04-07  
**Versão:** 1.0  
**Aprovação board:** Howard Marks (CCO) — sessão 2026-04-07  
**Modo:** Especificação — nova funcionalidade + renomeação

---

## BLOCO 1 — Contexto do projeto

Sistema: ATLAS — frontend React + backend FastAPI  
Camada: Frontend (`atlas_ui/`) + backend (`atlas_backend/`) + Delta Chaos via subprocess  
Tecnologias relevantes: React, Zustand (`systemStore.js`), FastAPI, `dc_runner.py`, WebSocket  
Regra inviolável: Delta Chaos nunca é importado diretamente — sempre via subprocess `dc_runner.py`

---

## BLOCO 2 — Situação atual

**2.1 — Aba Manutenção**

`atlas_ui/src/views/ManutencaoView.jsx` — aba atualmente chamada "Manutenção" no menu de navegação.

Contém hoje:
- **Onboarding de novo ativo** — formulário para iniciar sequência `backtest_dados → TUNE → backtest_gate`
- **Exportar** — botão sem nome preciso, função não especificada nesta sessão

Não contém:
- Seção de TUNE por ativo
- Lista de relatórios gerados
- Fluxo de aprovação de parâmetros
- Placeholder para Retomada de Estado E
- Qualquer indicador de elegibilidade ou estado pendente

**2.2 — TUNE**

`dc_runner.py` — `run_tune(ticker)` existe e chama `--modo tune` no `edge.py`.  
Não existe endpoint dedicado `/delta-chaos/tune` no backend.  
Não existe fluxo de aprovação — se TUNE rodar, não há etapa de revisão antes de gravar parâmetros.  
Não existe geração de relatório em `relatorios/`.

**2.3 — Relatórios**

Diretório `relatorios/` não existe.  
`relatorios/index.json` não existe.  
Nenhum módulo do Delta Chaos gera relatório `.md` estruturado hoje.

**2.4 — Aprovação de parâmetros**

Não existe fluxo de aprovação explícita pelo CEO antes de gravar TP/STOP no master JSON.  
Parâmetros não são gravados com confirmação — processo manual hoje.

---

## BLOCO 3 — Comportamento desejado

### 3.1 — Renomeação

Renomear a aba "Manutenção" para **"Gestão"** em todos os pontos:
- Label do menu de navegação
- Título interno da view
- Nome do arquivo: `ManutencaoView.jsx` → `GestaoView.jsx`
- Qualquer referência em `systemStore.js`, roteamento, ou outros componentes

### 3.2 — Estrutura visual da aba

A aba Gestão é organizada em duas seções distintas:

**Seção "Por Ativo"** — operações que afetam um ativo específico:
- Onboarding
- TUNE
- Retomada Estado E (placeholder)

**Seção "Sistema"** — operações globais:
- Relatórios
- Snapshot
- Backup

Cada item da seção "Por Ativo" exibe badge de estado visual:
- 🔴 Vermelho — requer ação imediata (bloqueado, falha)
- 🟡 Amarelo — elegível, aguarda decisão do CEO
- 🟢 Verde — em ordem, sem ação necessária
- ⚪ Cinza — inativo ou não aplicável

O CEO visualiza todos os badges sem scroll — a hierarquia visual de urgência orienta a ação.

Frequência visual: operações raras (Retomada E, Backup) devem ter peso visual menor que operações frequentes (TUNE, Relatórios).

### 3.3 — Seção TUNE

Lista todos os ativos em OPERAR com indicador de elegibilidade:

```
VALE3   🟡 Elegível   187 dias úteis   [Executar]
PETR4   🟢 Ok          43 dias úteis
BOVA11  🟢 Ok          67 dias úteis
```

**Fluxo completo do TUNE:**

```
1. CEO clica [Executar] no ativo elegível
2. Backend chama dc_runner.run_tune(ticker) via endpoint POST /delta-chaos/tune
3. Delta Chaos roda → gera RELATORIO_<ID>_<TICKER>_<CICLO>.md em relatorios/
4. index.json é atualizado com a nova entrada
5. Aba exibe: "Relatório gerado — aguardando aprovação CEO"
   Badge muda para 🟡 com label "Aguardando aprovação"
6. CEO baixa o relatório, leva ao board, delibera
7. CEO volta à aba → clica [Aplicar parâmetros]
8. Modal de confirmação exibe delta:
   "TP: 8.0% → 11.0% | STOP: 5.0% → 6.5% — Confirmar?"
9. CEO confirma → TP/STOP gravados no master JSON com escrita atômica
10. historico_config[] registra: data, módulo TUNE, valores anteriores e novos
11. Badge volta para 🟢 Ok — elegibilidade reiniciada
```

O botão [Aplicar parâmetros] só aparece após relatório gerado e não aplicado.  
O botão [Executar] fica desabilitado durante execução e após relatório gerado mas não aplicado.

### 3.4 — Seção Onboarding

Lista ativos em avaliação com pipeline de etapas visível:

```
BBAS3   backtest_dados ✓ | TUNE ✓ | backtest_gate ✗ E5 bloqueado   🔴 [Ver detalhe]
```

Cada etapa mostra: ✓ concluída, ✗ falhou (com código de erro), ⏳ em execução, ⚪ pendente.

Botão de ação disponível apenas quando há etapa executável — não quando bloqueado por falha que requer correção externa.

Transição para OPERAR após GATE 8/8 requer confirmação explícita do CEO — não é automática.  
Modal: "BBAS3 aprovado pelo GATE — confirmar entrada em OPERAR?"

Toda confirmação gera entrada em `historico_config[]`.

### 3.5 — Seção Retomada Estado E (placeholder)

Exibe ativos atualmente em estado E:

```
⚪ Nenhum ativo em estado E
```

Quando houver ativo em estado E:
```
🔴 VALE3 — Estado E desde 2026-03 — [Protocolo pendente de spec]
```

Botão desabilitado com tooltip: "Protocolo de retomada não implementado".  
A seção existe para quando a spec do protocolo for emitida — sem redesenho da aba.

### 3.6 — Seção Relatórios

Lista todos os relatórios gerados via `relatorios/index.json`:

```
#003   VALE3   2026-04   TUNE         2026-04-07   [Download]
#002   BBAS3   2026-04   ONBOARDING   2026-04-05   [Download]
#001   VALE3   2026-02   TUNE         2026-02-12   [Download]
```

Colunas: ID, Ticker, Ciclo, Tipo, Data de execução, Ação.  
Ordenado por ID decrescente — mais recente no topo.  
Download direto do arquivo `.md` — sem navegação no filesystem.

### 3.7 — Seção Sistema

**Snapshot** — exporta estado atual do sistema para sessão com board.  
**Backup** — exporta dados operacionais para segurança.  
Ambos são idempotentes — podem ser executados múltiplas vezes sem risco.  
Ambos exibem confirmação antes de executar com descrição do que será exportado.

### 3.8 — Geração de relatório pelo Delta Chaos

**Formato do arquivo:** `RELATORIO_<ID>_<TICKER>_<CICLO>.md`  
**Localização:** `relatorios/` na raiz do projeto Delta Chaos  
**ID:** sequencial, gerado a partir de `relatorios/index.json`

**Template do arquivo `.md`:**

```markdown
# Relatório Delta Chaos — <TICKER> — <CICLO>
**Tipo:** <TUNE | ONBOARDING | RETOMADA_E>
**ID:** <ID>
**Data de execução:** <YYYY-MM-DD>
**Gerado por:** Delta Chaos v1.0

---

## Como usar este relatório
Cole este arquivo numa sessão com o board Delta Chaos.
O board irá:
  1. Explicar os resultados apresentados
  2. Recomendar aplicar ou não os parâmetros sugeridos
  3. Abrir tensões se houver divergência entre regime e parâmetros

---

## Resumo executivo
**Ativo:** <TICKER>
**Período analisado:** <DATA_INICIO> a <DATA_FIM>
**Dias úteis analisados:** <N>
**Regime dominante:** <REGIME>

**Parâmetros atuais:**
  TP:   <TP_ATUAL>%
  STOP: <STOP_ATUAL>%

**Parâmetros sugeridos:**
  TP:   <TP_SUGERIDO>%   (delta: <+/-X>%)
  STOP: <STOP_SUGERIDO>% (delta: <+/-X>%)

**Recomendação:** <APLICAR | REVISAR | MANTER>

---

## Dados completos
```json
{
  "tipo": "<TUNE|ONBOARDING|RETOMADA_E>",
  "id": "<ID>",
  "ticker": "<TICKER>",
  "ciclo": "<CICLO>",
  "data_execucao": "<YYYY-MM-DD>",
  "periodo_analisado": {
    "inicio": "<YYYY-MM-DD>",
    "fim": "<YYYY-MM-DD>",
    "dias_uteis": <N>
  },
  "regime_dominante": "<REGIME>",
  "parametros_atuais": {
    "take_profit": <FLOAT>,
    "stop_loss": <FLOAT>
  },
  "parametros_sugeridos": {
    "take_profit": <FLOAT>,
    "stop_loss": <FLOAT>
  },
  "delta": {
    "take_profit": <FLOAT>,
    "stop_loss": <FLOAT>
  },
  "recomendacao": "<APLICAR|REVISAR|MANTER>",
  "detalhes": {}
}
```
```

**Schema do `relatorios/index.json`:**

```json
[
  {
    "id": "003",
    "ticker": "VALE3",
    "ciclo": "2026-04",
    "tipo": "TUNE",
    "data_execucao": "2026-04-07",
    "arquivo": "RELATORIO_003_VALE3_2026-04.md",
    "aplicado": false
  }
]
```

Campo `"aplicado": true` é gravado quando CEO confirma [Aplicar parâmetros].

### 3.9 — Endpoint backend

Criar `POST /delta-chaos/tune` em `atlas_backend/api/routes/delta_chaos.py`:

```python
@router.post("/tune")
async def tune_run(ticker: str):
    resultado = await dc_runner.run_tune(ticker)
    # após execução: gera relatório .md + atualiza index.json
    return resultado
```

Criar `POST /delta-chaos/tune/aplicar` para gravar parâmetros aprovados:

```python
@router.post("/tune/aplicar")
async def tune_aplicar(ticker: str, tp: float, stop: float):
    # grava TP/STOP no master JSON com escrita atômica
    # registra em historico_config[]
    # atualiza index.json campo "aplicado": true
    return {"status": "ok"}
```

### 3.10 — Auditoria universal

Toda ação executada via aba Gestão que altera o estado operacional do sistema gera entrada em `historico_config[]` do master JSON do ativo afetado:

```json
{
  "data": "2026-04-07",
  "modulo": "TUNE v1.0",
  "parametro": "take_profit",
  "valor_anterior": 8.0,
  "valor_novo": 11.0
}
```

Ações auditáveis: aplicar TUNE, confirmar entrada em OPERAR após onboarding, snapshot, qualquer futura ação de Retomada E.

---

## BLOCO 4 — O que não deve ser tocado

- `gate_eod.py` — sem modificações
- `gate.py` — sem modificações além do patch já especificado em SPEC_ATLAS_v2.6
- `TuneApprovalCard.jsx` — não modificar; o modal de confirmação de TUNE é novo componente
- `useWebSocket.js` — sem modificações
- `AtivosTable.jsx`, `PosicoesTable.jsx` — sem modificações
- Lógica interna de `executar_tune()` em `edge.py` — sem modificações
- Os três books (`book_backtest`, `book_paper`, `book_live`) — invioláveis
- Escrita atômica (`tempfile + os.replace`) em todos os JSONs — obrigatória
- `relatorios/index.json` nunca sobrescrito — apenas append de novas entradas

---

*Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*  
*Spec v1.0 — 2026-04-07*  
*Pré-requisito: SPEC_RENOMEACAO aplicada antes desta*
