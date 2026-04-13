# SPEC — Nav "Relatório" na Aba Ativo + Relatório de TUNE exportável
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board
**Data:** 2026-04-13
**Versão:** 1.0
**Modo:** Especificação — nova funcionalidade

---

## BLOCO 1 — Contexto do projeto

Sistema: ATLAS — frontend React + backend FastAPI
Camada: Frontend (`atlas_ui/src/components/AtivoView.jsx`), backend (`atlas_backend/`)
Tecnologias relevantes: React, FastAPI, Markdown
Regra inviolável: Delta Chaos nunca é importado diretamente — sempre via subprocess

---

## BLOCO 2 — Situação atual

**Frontend — AtivoView.jsx:**
- Dropdown de seleção de ativo + quatro tabs: ORBIT | REFLECT | CICLOS | ANALYTICS
- Tabs são botões no array `["orbit", "reflect", "ciclos", "analytics"]`
- Nenhuma tab de relatório existe

**Backend:**
- Não existe endpoint para geração de relatório de TUNE por ativo
- Não existe diretório `relatorios/` nem `relatorios/index.json`
- `historico_config[]` existe no master JSON de cada ativo — registra histórico de aplicações de TUNE

**Dados disponíveis no master JSON por ativo:**
- `historico_config[]` — histórico de TUNEs aplicados com TP, STOP, IR, trials, confiança, janela, reflect_mask
- `reflect_cycle_history` — estado REFLECT por ciclo
- `historico[]` — ciclos ORBIT com regime e IR
- `take_profit`, `stop_loss` — parâmetros vigentes

---

## BLOCO 3 — Comportamento desejado

### 3.1 — Nova tab "RELATÓRIO" em AtivoView.jsx

Adicionar `"relatorio"` ao array de tabs em `AtivoView.jsx`:

```jsx
{["orbit", "reflect", "ciclos", "analytics", "relatorio"].map((tab) => (
  // botão existente — sem alteração de estilo
))}
```

A tab RELATÓRIO exibe o componente `RelatorioTab` descrito abaixo.

### 3.2 — Componente RelatorioTab

Exibe o relatório de TUNE mais recente do ativo selecionado. Se não houver TUNE registrado, exibe mensagem: "Nenhum TUNE executado para este ativo."

**Layout:**

```
┌─────────────────────────────────────────────────┐
│ RELATÓRIO DE TUNE — VALE3                       │
│ Gerado em: 2026-04-13   [Exportar .md]          │
├─────────────────────────────────────────────────┤
│ DIAGNÓSTICO EXECUTIVO                           │
│ [parágrafo gerado a partir dos dados — ver 3.3] │
├─────────────────────────────────────────────────┤
│ PARÂMETROS TUNE                                 │
│ TP atual: 0.75   →   TP sugerido: 0.80  (+0.05) │
│ STOP atual: 1.50 →   STOP sugerido: 1.75 (+0.25)│
├─────────────────────────────────────────────────┤
│ QUALIDADE DA OTIMIZAÇÃO                         │
│ IR válido: +1.234  │ N trades: 47  │ Alta        │
│ Janela: 5 anos (2021–2026)                      │
│ Trials rodados: 187 / 200  (early stop: SIM)    │
│ Study retomado: NÃO                             │
├─────────────────────────────────────────────────┤
│ MÁSCARA REFLECT                                 │
│ 12 ciclos mascarados de 58 (20.7%)              │
│ Ciclos com REFLECT real: 46 │ Fallback B: 12    │
├─────────────────────────────────────────────────┤
│ DISTRIBUIÇÃO DE SAÍDAS (janela de teste)        │
│ TP: 31 (66%)  │ STOP: 9 (19%)  │ VENC: 7 (15%) │
│ Acerto: 73.2%                                   │
├─────────────────────────────────────────────────┤
│ PIOR TRADE (janela de teste)                    │
│ Data: 2023-03-15  Motivo: STOP  P&L: -R$412     │
├─────────────────────────────────────────────────┤
│ HISTÓRICO DE TUNEs APLICADOS                    │
│ 2026-04-13  TP=0.75 STOP=1.50  IR=+1.123  Alta  │
│ 2026-01-08  TP=0.70 STOP=1.50  IR=+0.987  Baixa │
└─────────────────────────────────────────────────┘
```

### 3.3 — Diagnóstico executivo (gerado pelo backend)

O backend gera um parágrafo de diagnóstico em linguagem natural baseado nas regras abaixo. Não usa IA — é template determinístico.

**Regras de geração:**

```
SE ir_valido >= 1.0 E confianca == "alta":
    → "Edge forte confirmado. TUNE sugere ajuste de TP/STOP com alta confiança estatística (N={n}). Recomendação: APLICAR."

SE ir_valido >= 0.5 E confianca == "baixa":
    → "Edge positivo com amostra limitada (N={n}). Ajuste sugerido é plausível mas incerto. Recomendação: REVISAR com board antes de aplicar."

SE ir_valido < 0.5:
    → "IR válido abaixo de 0.5. Parâmetros atuais podem ser superiores ao sugerido. Recomendação: MANTER parâmetros atuais."

SE confianca == "amostra_insuficiente":
    → "Amostra insuficiente (N={n} < 20). Resultado não confiável. Recomendação: NÃO APLICAR — aguardar mais ciclos."

SE reflect_mask_pct > 30%:
    → Acrescentar: " Atenção: {reflect_mask_pct:.0f}% dos ciclos foram mascarados pelo REFLECT — IR válido pode estar inflado."

SE janela_anos <= 3:
    → Acrescentar: " Atenção: janela de {janela_anos} anos (Optuna) exclui ciclos anteriores a {ano_teste_ini} — eventos extremos históricos não estão no cálculo."
```

### 3.4 — Aviso sobre proxies de simulação

Exibir sempre, em destaque âmbar, abaixo do diagnóstico executivo:

> "Os valores de TP e STOP foram otimizados usando proxies intradiários: mínimo do dia como proxy de TP e máximo do dia como proxy de STOP. Em dias de alta volatilidade, esses proxies podem superestimar ganhos de TP e subestimar custos de STOP."

Esta limitação deve aparecer no diagnóstico executivo — não apenas em nota de rodapé.

### 3.5 — Botão [Exportar .md]

Ao clicar, gera e faz download de um arquivo `.md` com o conteúdo completo do relatório.

**Nome do arquivo:** `TUNE_{TICKER}_{CICLO}_{DATA}.md`
Exemplo: `TUNE_VALE3_2026-04_2026-04-13.md`

**Conteúdo do arquivo exportado:**

```markdown
# Relatório de TUNE — {TICKER} — {CICLO}
**Data de execução:** {DATA}
**Gerado por:** ATLAS v2.6

---

## Como usar este relatório
Cole este arquivo numa sessão com o board Delta Chaos.
O board irá:
1. Avaliar os resultados apresentados
2. Recomendar APLICAR, REVISAR ou MANTER os parâmetros
3. Abrir tensões se houver divergência entre regime e parâmetros

---

## ⚠️ Limitação de simulação
Os valores foram otimizados usando proxies intradiários: mínimo do dia
como proxy de TP e máximo do dia como proxy de STOP. Em dias de alta
volatilidade, esses proxies podem superestimar ganhos de TP e
subestimar custos de STOP.

---

## Diagnóstico executivo
{DIAGNOSTICO_EXECUTIVO}

---

## Parâmetros TUNE
| Campo         | Atual  | Sugerido | Delta  |
|---------------|--------|----------|--------|
| Take Profit   | {TP_ATUAL} | {TP_NOVO} | {DELTA_TP} |
| Stop Loss     | {STOP_ATUAL} | {STOP_NOVO} | {DELTA_STOP} |

---

## Qualidade da otimização
- IR válido (janela de teste): {IR_VALIDO}
- N trades na janela: {N_TRADES}
- Confiança: {CONFIANCA}
- Janela de teste: {JANELA_ANOS} anos ({ANO_TESTE_INI}–{ANO_ATUAL})
- Trials rodados: {TRIALS_RODADOS} / {TRIALS_TOTAL}
- Early stop ativado: {EARLY_STOP}
- Study Optuna retomado: {RETOMADO}

---

## Máscara REFLECT
- Ciclos mascarados (Edge C/D/E): {REFLECT_MASK} de {TOTAL_CICLOS} ({REFLECT_MASK_PCT:.1f}%)
- Ciclos com REFLECT real: {CICLOS_REAIS}
- Ciclos com fallback B: {CICLOS_FALLBACK}

---

## Distribuição de saídas (janela de teste)
- Take Profit: {N_TP} ({PCT_TP:.1f}%)
- Stop Loss: {N_STOP} ({PCT_STOP:.1f}%)
- Vencimento: {N_VENC} ({PCT_VENC:.1f}%)
- Acerto: {ACERTO_PCT:.1f}%

---

## Pior trade (janela de teste)
- Data: {PIOR_DATA}
- Motivo: {PIOR_MOTIVO}
- P&L: R${PIOR_PNL:,.2f}

---

## Histórico de TUNEs aplicados
| Data | TP | STOP | IR válido | Confiança |
|------|-----|------|-----------|-----------|
{HISTORICO_TUNE_TABELA}

---

## Dados brutos (JSON)
```json
{JSON_COMPLETO}
```
```

### 3.6 — Endpoint backend

Criar em `atlas_backend/api/routes/delta_chaos.py` (ou novo arquivo de rotas):

**GET /ativos/{ticker}/relatorio-tune**
```python
# Lê historico_config[] do master JSON
# Filtra registros com modulo == "TUNE v2.0"
# Monta payload completo do relatório incluindo diagnóstico determinístico
# Retorna: dict com todos os campos necessários para renderização e exportação
```

O endpoint deve retornar o relatório do TUNE mais recente por padrão. Se `?historico=true`, retorna lista de todos os TUNEs executados.

---

## BLOCO 4 — O que não deve ser tocado

- Tabs existentes (orbit, reflect, ciclos, analytics) — sem modificações de conteúdo
- `AtivoView.jsx` — apenas adicionar a nova tab e o novo componente; não alterar lógica existente
- `WalkForwardChart.jsx`, `DistributionChart.jsx`, `ACFChart.jsx`, `TailMetrics.jsx` — sem modificações
- Master JSON dos ativos — este endpoint é read-only; não escreve nada
- `historico_config[]` — apenas leitura neste contexto

---

*Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*
*Spec v1.0 — 2026-04-13*
