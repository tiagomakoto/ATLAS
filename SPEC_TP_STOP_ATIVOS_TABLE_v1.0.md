# SPEC — TP/STOP visível na tabela de Ativos (Visão Geral)
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board
**Data:** 2026-04-13
**Versão:** 1.0
**Modo:** Cirúrgico — adição de colunas em componente existente

---

## BLOCO 1 — Contexto do projeto

Sistema: ATLAS — frontend React + backend FastAPI
Camada: Frontend (`atlas_ui/src/components/AtivosTable.jsx`) + backend (`atlas_backend/`)
Tecnologias relevantes: React, FastAPI

---

## BLOCO 2 — Situação atual

**AtivosTable.jsx:**
- Tabela na aba Visão Geral com colunas existentes: Ativo, Status, Regime, REFLECT, Sizing, e possivelmente outras
- Não exibe TP nem STOP vigentes por ativo
- TP e STOP estão disponíveis nos campos `take_profit` e `stop_loss` do master JSON de cada ativo em `ATIVOS_DIR/{TICKER}.json`

**Endpoint existente:**
- `GET /ativos` — retorna lista de tickers
- `GET /ativos/{ticker}` — retorna dados completos do ativo incluindo `take_profit` e `stop_loss`

---

## BLOCO 3 — Comportamento desejado

### 3.1 — Novas colunas na AtivosTable

Adicionar duas colunas ao final da tabela existente:

| Coluna | Fonte | Formato |
|--------|-------|---------|
| TP | `take_profit` do master JSON | número com 2 casas decimais. Ex: `0.75` |
| STOP | `stop_loss` do master JSON | número com 2 casas decimais. Ex: `1.50` |

**Exibição:**
- Valores exibidos em fonte monospace, alinhados à direita
- Se o campo não existir no JSON: exibir `—` em cinza
- Sem badge, sem colorização — são parâmetros de configuração, não indicadores de estado

### 3.2 — Backend

Se o endpoint `GET /ativos` já retorna `take_profit` e `stop_loss` por ativo, nenhuma alteração backend é necessária.

Se não retorna, adicionar esses campos ao response do endpoint `GET /ativos` (não criar novo endpoint).

Verificar antes de implementar — não criar endpoint desnecessário.

---

## BLOCO 4 — O que não deve ser tocado

- Colunas existentes da AtivosTable — sem reordenação, sem remoção
- Lógica de status, regime, REFLECT e sizing — sem alterações
- `PosicoesTable.jsx` — fora do escopo
- Master JSON dos ativos — este componente é read-only

---

*Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*
*Spec v1.0 — 2026-04-13*
