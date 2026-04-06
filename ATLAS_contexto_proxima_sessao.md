# ATLAS — Prompt de Contexto para Próxima Sessão
# Foco: UX/UI — Continuação de Implementação

**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board
**Data:** 2026-04-04
**Versão corrente do ATLAS:** v2.5.3 (patch em implementação)

---

## 1. O QUE É O ATLAS

Dashboard supervisório (não painel de ações) para o Delta Chaos —
sistema quant de venda de volatilidade na B3. Stack: FastAPI backend
+ React frontend + WebSocket. CEO Tiago é o único operador.

**Repositório:** `tiagomakoto/ATLAS`
**Backend:** `atlas_backend/` (FastAPI + uvicorn)
**Frontend:** `atlas_ui/` (React)

**Princípio central:** ATLAS observa e informa. Não executa por conta
própria. Os únicos pontos de contato operador↔sistema são:

- **A)** Depositar arquivo xlsx em `opcoes_hoje/` + clicar Check Status
- **B)** Declarar novo ativo para onboarding
- **C)** Aprovar resultado do TUNE (um clique)

---

## 2. ARQUITETURA

### paths.json (`atlas_backend/config/paths.json`)
```json
{
  "config_dir":       "G:\\Meu Drive\\Delta Chaos\\ativos",
  "ohlcv_dir":        "G:\\Meu Drive\\Delta Chaos\\TAPE\\ohlcv",
  "history_dir":      "G:\\Meu Drive\\Delta Chaos\\history",
  "book_dir":         "G:\\Meu Drive\\Delta Chaos\\BOOK",
  "delta_chaos_base": "G:\\Meu Drive\\Delta Chaos",
  "delta_chaos_dir":  "G:\\Meu Drive\\Delta Chaos\\delta_chaos"
}
```

### Delta Chaos — módulos .py (nunca importar diretamente no ATLAS)
```
init.py   → bootstrap, carregar_config()
tape.py   → OHLCV, COTAHIST, SELIC, REFLECT daily+cycle, BS vetorizado
orbit.py  → regime: ALTA/BAIXA/NEUTRO_BULL/NEUTRO_BEAR/NEUTRO_LATERAL/
             NEUTRO_MORTO/NEUTRO_TRANSICAO/RECUPERACAO/PANICO
fire.py   → seleção de opção, legs, TP/STOP/vencimento
gate.py   → validação 8 etapas (OPERAR/MONITORAR/EXCLUÍDO)
gate_eod.py → verificação leve diária
book.py   → 3 books separados: book_backtest / book_paper / book_live
edge.py   → orquestrador Delta Chaos
tune.py   → calibração TP/STOP a cada 126 dias úteis
```

**Regra inviolável:** Delta Chaos roda como subprocess do ATLAS via
`core/dc_runner.py`. Nunca importado diretamente.

### Ativos ativos
| Ticker | TP   | STOP | GATE    | Status          |
|--------|------|------|---------|-----------------|
| VALE3  | 0.90 | 2.0x | 8/8     | Operacional     |
| PETR4  | 0.90 | 2.0x | 8/8     | Operacional     |
| BOVA11 | 0.75 | 1.5x | 8/8     | Paper trading   |
| BBAS3  | 0.75 | 1.5x | 7/8 ✗E5 | Bloqueado GATE  |

---

## 3. NAVEGAÇÃO ATUAL (v2.5.2 — estado aprovado)

```
Abas globais:
  [ Delta Chaos ] [ Cripto · ] [ Buy & Hold · ] [ Trending · ]

Abas internas Delta Chaos:
  [ Visão Geral ] [ Ativo ] [ Manutenção ]

Sub-abas de Ativo:
  [ ORBIT ] [ REFLECT ] [ CICLOS ] [ ANALYTICS ]
```

**Aba Terminal** foi decidida para v2.6 (não implementar ainda).

---

## 4. VISÃO GERAL — 6 BLOCOS EM ORDEM

```
1. Botão CHECK STATUS + timestamp última run
2. OrchestratorProgress  ← visível só quando rodando
3. DigestPanel           ← persiste após run
4. TuneApprovalCard      ← se TUNE pendente
5. Tabela Ativos Parametrizados
6. Tabela Posições Abertas — PAPER (seletor PAPER/LIVE)
```

---

## 5. LÓGICA DO CHECK STATUS — FONTE DE VERDADE

Ao clicar CHECK STATUS o backend executa esta sequência via
`POST /orchestrator/run → core/orchestrator.py`:

```
V0 → ORBIT → REFLECT → TUNE → GATE → EOD
```

**V0 — Guarda:** posição aberta + arquivo xlsx desatualizado →
header vermelho + bloqueia EOD

**Passo 1 — ORBIT:** para cada ativo, lê `historico[-1].ciclo_id`.
Se `< YYYY-MM atual` → roda `run_orbit(ticker)`

**Passo 2 — REFLECT:** lê `reflect_all_cycles_history[-1].ciclo_id`.
Se desatualizado → avisa no digest (roda automaticamente no EOD)

**Passo 3 — TUNE:** calcula staleness via `pd.bdate_range`.
Se `>= 126 dias úteis` → roda `run_tune(ticker)` → emite card aprovação

**Passo 4 — GATE:** se `(hoje - ultima_gate).days > 30` →
roda `run_gate(ticker)`

**Passo 5 — EOD:** se V0 limpo e xlsx presente em `opcoes_hoje/` →
roda `run_eod(xlsx_dir)`

Cada passo emite eventos WebSocket para atualizar UI em tempo real.

---

## 6. SCHEMAS REAIS DOS ARQUIVOS

### `{TICKER}.json` (em `ativos/`)
```json
{
  "ativo": "VALE3",
  "take_profit": 0.90,
  "stop_loss": 2.0,
  "historico": [
    {
      "ciclo_id": "2025-03",
      "regime": "NEUTRO_BULL",
      "ir": 0.389,
      "sizing": 0.5,
      "score": 0.72,
      "vol_21d": 0.28,
      "vol_63d": 0.25,
      "s1": ..., "s2": ..., "s3": ..., "s4": ..., "s5": ..., "s6": ...
    }
  ],
  "reflect_historico": [
    {
      "ciclo_id": "2025-03",
      "reflect_state": "B",
      "reflect_score": 0.61,
      "aceleracao": -0.02,
      "delta_ir": 0.01,
      "iv_prem_ratio": null,
      "ret_vol_ratio": null
    }
  ],
  "historico_config": [
    {
      "modulo": "TUNE v1.1",
      "data": "2025-10-01",
      "valor_novo": "TP=0.90 STOP=2.0"
    },
    {
      "modulo": "GATE",
      "data": "2026-03-01",
      "valor_novo": "8/8 OPERAR"
    }
  ],
  "reflect_permanent_block_flag": false
}
```

**Nota:** `iv_prem_ratio` e `ret_vol_ratio` são `null` até que
`tape_reflect_daily()` EOD esteja ativo — comportamento esperado.

### `book_paper.json` (em `BOOK/`)
```json
{
  "fonte": "paper",
  "capital": 10000,
  "counter": 1,
  "ops": [
    {
      "op_id": "B0001",
      "core": {
        "ativo": "BOVA11",
        "estrategia": "BEAR_CALL_SPREAD",
        "data_entrada": "2026-03-28",
        "data_saida": null,
        "pnl": null
      },
      "orbit": {
        "ciclo": "2026-03",
        "regime_entrada": "NEUTRO_BEAR",
        "ir_orbit": 0.389,
        "sizing_orbit": 0.5
      },
      "legs": [
        {
          "tipo": "CALL",
          "posicao": "vendida",
          "ticker": "BOVAH220",
          "strike": 118.0,
          "vencimento": "2026-03-20",
          "premio_entrada": 1.25,
          "delta": -0.32,
          "gamma": 0.08,
          "theta": 0.04,
          "vega": 0.18,
          "iv": 0.24
        }
      ]
    }
  ]
}
```

---

## 7. ENDPOINTS IMPLEMENTADOS (ou especificados para implementar)

```
GET  /ativos                         → lista tickers
GET  /ativos/{ticker}                → master JSON do ativo
POST /ativos/{ticker}/update         → edita config (confirm obrigatório)
GET  /ativos/book?fonte=paper|live   → book
POST /orchestrator/run               → Check Status (V0→ORBIT→REFLECT→TUNE→GATE→EOD)
GET  /orchestrator/status            → estado atual sem executar
POST /delta-chaos/gate               → run GATE isolado
POST /delta-chaos/tune               → run TUNE isolado
POST /delta-chaos/orbit              → run ORBIT isolado
POST /delta-chaos/eod                → run EOD isolado
POST /delta-chaos/onboarding         → TAPE→ORBIT→TUNE→GATE para novo ativo
POST /report                         → exportar relatório MD
WS   /ws                             → WebSocket eventos em tempo real
```

**Todos os POST com payload:** `{ confirm: true, description: "..." }`
(auditoria — rejeitar se `confirm = false`)

---

## 8. COMPONENTES REACT EXISTENTES (ou especificados)

```
VisaoGeral.jsx          ← 6 blocos, Check Status, Digest, TuneApproval
OrchestratorProgress.jsx← barra de progresso por tarefa (1/5 a 5/5)
DigestPanel.jsx         ← resumo pós-run (ok/alerta/bloqueado/pendente)
TuneApprovalCard.jsx    ← card âmbar com TP/STOP atual vs sugerido
AtivosTable.jsx         ← tabela ativos parametrizados
PosicoesTable.jsx       ← posições abertas com seletor PAPER/LIVE
OrbitTab.jsx            ← regime atual + histórico de ciclos
ReflectTab.jsx          ← estado REFLECT A-E + scores
CiclosTab.jsx           ← walk-forward por ciclo
AnalyticsTab.jsx        ← distribuição IR, retornos, ACF, kurtosis
ManutencaoView.jsx      ← onboarding novo ativo + exportar
ConfigEditor.jsx        ← edita só TP e Stop Loss (TUNE gera, não manual)
```

### CSS Variables (paleta — não alterar)
```css
--atlas-bg:               #0a0e1a
--atlas-surface:          #111827
--atlas-border:           #1e2a3a
--atlas-text-primary:     #e2e8f0
--atlas-text-secondary:   #64748b
--atlas-blue:             #3b82f6
--atlas-green:            #10b981
--atlas-red:              #ef4444
--atlas-amber:            #f59e0b
```

Fonte: `monospace` em todo o sistema. Sem serif, sem sans-serif.

---

## 9. REGRAS DE NEGÓCIO INVARIANTES

- Três books separados são **invioláveis** (backtest / paper / live)
- Todos os JSON writes são **atômicos** (tempfile + os.replace)
- `NEUTRO_LATERAL` e `NEUTRO_MORTO` → `sizing = 0.0`
- REFLECT é **passivo** em backtests — nunca injeta sizing histórico
- REFLECT estado E → bloqueia permanentemente até protocolo de 5 gates
  (protocolo não implementado ainda — sem UI para isso)
- `volume > 0` como filtro de liquidez (não filtro financeiro mínimo)
- Opções filtradas para **vencimento mensal** antes de salvar
- Decisões de GATE, TUNE, ORBIT nunca são revertidas manualmente —
  apenas via novo ciclo do módulo correspondente
- ConfigEditor expõe **apenas TP e Stop Loss** — nenhum outro parâmetro
- Threshold GATE de 0.6 está **hardcoded** em `gatekeeper.py`;
  slider em AnalyticsTab é simulador, não altera valor real

---

## 10. PENDÊNCIAS ABERTAS

### Críticas (bloqueia operação)
- [ ] **v2.5.3** `orchestrator.py` completo → registrar em `main.py`
      Problema: `POST /orchestrator/run` retorna 404 ou não executa
      a sequência de verificação
- [ ] Remover `BOVA11_corrupto_*` de `ativos/` (aparece na tabela)

### UX/UI — próximas sessões
- [ ] Header vermelho quando V0 detecta posição sem arquivo EOD
- [ ] OrchestratorProgress com segmentos por tarefa (não barra única)
- [ ] DigestPanel com ícones por tipo (✓ ok / ⚠ alerta / ✗ bloqueado / ~ pendente)
- [ ] TuneApprovalCard: comparação visual atual vs sugerido (âmbar)
- [ ] Tooltips em `iv_prem_ratio` e `ret_vol_ratio` no ReflectTab
      (null = aguardando EOD — isso é normal, não é erro)
- [ ] AnalyticsTab: renomear slider para "Simulador de threshold"
      (não altera valor real)
- [ ] AnalyticsTab: eixo X do walk-forward = `ciclo_id` (ex: 2024-03),
      não índice numérico
- [ ] ACF: série histórica completa, sem seletor temporal
- [ ] Posições Abertas: seletor PAPER/LIVE visível e funcional

### Arquitetura futura (não implementar agora)
- [ ] **v2.6** Terminal de comandos — aba global ao lado de Trending
      Comando: `init {sistema} {comando} {argumento}`
      Sandboxed — apenas comandos registrados por sistema
      Output: JSON para diagnóstico, MD para relatórios
- [ ] BBAS3: onboarding completo após GATE E5 ser resolvido
- [ ] Integração Telegram (hook `header_alert` já especificado no backend)
- [ ] TUNE v2.0: REFLECT cycle mask + estratégia por regime
      (só após primeiro trimestre de paper trading)
- [ ] REFLECT estado E: protocolo de retomada — não implementar até
      decisão do board

---

## 11. O QUE NÃO FAZER

- **Nunca** importar módulos Delta Chaos diretamente no ATLAS —
  sempre via subprocess / `dc_runner.py`
- **Nunca** expor botões RUN individuais na interface normal
  (GATE, TUNE, ORBIT, EOD isolados → v2.6 Terminal)
- **Nunca** editar JSON manualmente — sempre via endpoints com `confirm`
- **Nunca** exibir `iv_prem_ratio` ou `ret_vol_ratio` como erro
  quando forem `null` — isso é comportamento esperado
- **Nunca** permitir edição de TP/Stop fora do fluxo TUNE
- **Não** implementar aba Terminal agora (v2.6)
- **Não** implementar protocolo REFLECT estado E (decisão pendente)

---

## 12. FLUXO DE APROVAÇÃO DE CÓDIGO

Nenhuma versão de código é aprovada sem pronunciamento de SCAN
(Peter Müller + Margaret Hamilton + Dan Abramov).
Prompts gerados por Lilian Weng → implementação → SCAN → CEO aprova.

---

*Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*
*Handoff para próxima sessão — foco UX/UI ATLAS*
*Base: v2.5.3 | Data: 2026-04-04*
