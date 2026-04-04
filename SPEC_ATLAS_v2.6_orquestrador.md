# SPEC ATLAS v2.6 — Orquestrador de Atualização Mensal
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board  
**Data:** 2026-04-04  
**Versão:** 1.1 (patch — esclarecimentos Plan)  
**Aprovação board:** Howard Marks (CCO) — sessão 2026-04-04

---

## PROMPT 1 — Backend: novo fluxo do orquestrador + patch gate.py

---

### BLOCO 1 — Contexto do projeto

Sistema: ATLAS — backend FastAPI + subprocess Delta Chaos  
Camada: backend (`atlas_backend/`) + módulo Delta Chaos (`delta_chaos/gate.py`)  
Tecnologias relevantes: FastAPI, asyncio, subprocess via `dc_runner.py`, WebSocket `/ws/logs`  
Regra inviolável: Delta Chaos nunca é importado diretamente — sempre via subprocess `dc_runner.py`

---

### BLOCO 2 — Situação atual

**2.1 — Endpoint orquestrador**

`atlas_backend/api/routes/delta_chaos.py` — função `orchestrator_run()` (decorator `@router.post("/orchestrator/run")`)

O endpoint atual verifica staleness de ORBIT e REFLECT por timestamp e roda o que estiver defasado. Não há sequenciamento com dependências explícitas entre passos. Não há distinção entre fluxo diário e fluxo mensal. Não há loop por ativo — trata como operação única.

**2.2 — Modos CLI do edge.py**

`delta_chaos/edge.py` — bloco `if __name__ == "__main__"` com `argparse`

Modos atuais:
- `--modo eod` → paper/live diário
- `--modo eod_preview` → preview sem executar
- `--modo orbit` → instancia EDGE completo com `modo="backtest"`, apaga `book_backtest.json`, pesado
- `--modo gate` → chama `executar_gate(ticker)` diretamente
- `--modo tune` → chama `executar_tune(ticker)` diretamente
- `--modo reflect` → chama `executar_gate(ticker)` (incorreto — reflect_cycle não é gate)

**2.3 — dc_runner.py**

`atlas_backend/core/dc_runner.py` — função `run_orbit()` chama `--modo orbit` (modo pesado incorreto para atualização mensal)

**2.4 — gate.py — ausência de registro de falha**

`delta_chaos/gate.py` — função `executar_gate(ticker)`

Quando falha em E0 (cobertura mínima) ou E0-estratégias (sem estratégias configuradas), lança `ValueError` sem registrar o evento no `historico_config[]` do master JSON do ativo. O erro vai apenas para `audit.log` via `dc_runner.py`. O master JSON não tem rastro da tentativa.

**2.5 — dc_runner.py — funções ausentes**

`atlas_backend/core/dc_runner.py` — não existe `run_reflect_daily()` nem `run_gate_eod()`.

- `run_reflect_daily()` é necessário para o step diário de alimentação do REFLECT sem acionar o fluxo EOD completo.
- `run_gate_eod()` é necessário para o orquestrador chamar a guarda leve diária (`gate_eod.py`) via subprocess por ativo.

---

### BLOCO 3 — Comportamento desejado

**3.1 — Renomeação de modos CLI no edge.py**

Renomear os `choices` do argparse e os handlers correspondentes:

| Modo atual | Modo novo | Descrição |
|---|---|---|
| `orbit` | `backtest_dados` | COTAHIST + ORBIT completo — exclusivo para onboarding |
| *(não existe)* | `orbit` | OHLCV cache via yfinance + ORBIT + tape_reflect_cycle — atualização mensal |
| `gate` | `backtest_gate` | backtest completo + 8 etapas GATE — onboarding e atualização mensal |
| `eod` | `eod` | mantém |
| `eod_preview` | `eod_preview` | mantém |
| `tune` | `tune` | mantém |
| `reflect` | *(remover)* | incorreto — coberto pelo novo `--modo orbit` |
| *(não existe)* | `reflect_daily` | chama `tape_process_eod_file(xlsx_path)` para um ativo — exclusivo para step diário |

**Implementação do novo `--modo reflect_daily`:**

```python
elif args.modo == "reflect_daily":
    # Requer --ticker e --xlsx_path
    if not args.ticker or not args.xlsx_path:
        print("ERRO: --ticker e --xlsx_path obrigatorios para reflect_daily", file=sys.stderr)
        sys.exit(1)
    tape_process_eod_file(args.xlsx_path)
```

Adicionar `--xlsx_path` ao argparse como argumento opcional (usado apenas por `reflect_daily`).

**Implementação do novo `--modo orbit`:**

```python
elif args.modo == "orbit":
    # Não instancia EDGE — não apaga books
    anos = (list(map(int, args.anos.split(",")))
            if args.anos
            else list(range(2002, datetime.now().year + 1)))
    cfg_ativo = tape_carregar_ativo(args.ticker)
    df_ohlcv = tape_ohlcv(args.ticker, anos)  # usa cache, incrementa via yfinance
    df_ibov = tape_ibov(anos)
    orbit = ORBIT(universo={args.ticker: cfg_ativo})
    orbit.rodar(df_ohlcv, anos, modo="mensal")
    tape_reflect_cycle(args.ticker, datetime.now().strftime("%Y-%m"))
```

O `--modo backtest_dados` mantém o comportamento atual do `--modo orbit` (instancia EDGE completo).

**3.2 — dc_runner.py — novas funções**

Adicionar função `run_orbit_update(ticker, anos=None)` que chama `--modo orbit` (novo modo leve).  
Manter `run_orbit()` existente apontando para `--modo backtest_dados` — usado pelo onboarding.

```python
async def run_orbit_update(ticker: str, anos: Optional[list] = None) -> dict:
    script = _get_dc_script()
    args = ["-m", "delta_chaos.edge", "--modo", "orbit", "--ticker", ticker]
    if anos:
        args += ["--anos", ",".join(str(a) for a in anos)]
    return await _stream_subprocess(
        args=args,
        cwd=script.parent,
        action_name="dc_orbit_update",
        action_payload={"ticker": ticker, "anos": anos}
    )
```

Adicionar função `run_reflect_daily(ticker, xlsx_path)` que chama `--modo reflect_daily`:

```python
async def run_reflect_daily(ticker: str, xlsx_path: str) -> dict:
    script = _get_dc_script()
    return await _stream_subprocess(
        args=["-m", "delta_chaos.edge", "--modo", "reflect_daily",
              "--ticker", ticker, "--xlsx_path", xlsx_path],
        cwd=script.parent,
        action_name="dc_reflect_daily",
        action_payload={"ticker": ticker, "xlsx_path": xlsx_path}
    )
```

Adicionar função `run_gate_eod(ticker)` que chama `--modo gate_eod`:

```python
async def run_gate_eod(ticker: str) -> dict:
    script = _get_dc_script()
    return await _stream_subprocess(
        args=["-m", "delta_chaos.edge", "--modo", "gate_eod", "--ticker", ticker],
        cwd=script.parent,
        action_name="dc_gate_eod",
        action_payload={"ticker": ticker}
    )
```

Para `run_gate_eod` adicionar também `--modo gate_eod` no argparse do `edge.py`:

```python
elif args.modo == "gate_eod":
    from delta_chaos.gate_eod import gate_eod
    resultado = gate_eod(args.ticker, verbose=True)
    print(f"[GATE_EOD] {args.ticker}: {resultado}")
```

**3.3 — Novo fluxo do orquestrador**

Substituir a lógica de `orchestrator_run()` pelo seguinte fluxo, executado sequencialmente por ativo:

```
PARA CADA ativo em list_ativos():

  [DIÁRIO]

  1. tape_reflect_daily — via run_reflect_daily(ticker, xlsx_path)
     Detecção de xlsx: os.path.join(OPCOES_HOJE_DIR, f"{ticker}.xlsx")
     — só executa se arquivo existe
     — se ausente: digest registra "sem xlsx — reflect_daily pulado"

  2. Verificar posição aberta — lê book_paper.json
     Posição aberta: ops[].core.data_saida == null E ops[].core.ativo == ticker
     Preço entrada: ops[].legs[0].premio_entrada
     TP e STOP: master JSON ativos/{ticker}.json — campos "take_profit" e "stop_loss" na raiz
     Preço atual: coluna "fechamento" do xlsx EOD — fonte verdade de preço de mercado

     SE posição aberta:
       — calcular pnl_atual com preço do xlsx
       — se pnl_pct >= take_profit OU pnl_pct <= -stop_loss:
           fechar ordem → digest registra fechamento com motivo → fim para este ativo
       — se não atingido: digest registra P&L atual → fim para este ativo
     SE sem posição:
       — ir para step 3

  3. gate_eod (leve) — via run_gate_eod(ticker)
     Retorno esperado: "OPERAR" | "MONITORAR" | "BLOQUEADO" | "GATE VENCIDO"
     — SE "OPERAR": sinalizar no digest → aguarda ação do CEO (não abre automaticamente)
     — SE outros: digest registra motivo → fim para este ativo

  [MENSAL — só se ciclo mudou]
  Detecção: df = pd.read_parquet(OHLCV_DIR / f"{ticker}.parquet")
            ohlcv_date = df.index.max()
            ultimo_ciclo = dados["historico"][-1]["ciclo_id"]  # de ativos/{ticker}.json
            ciclo_mudou = ohlcv_date.strftime("%Y-%m") > ultimo_ciclo

  4. run_orbit_update(ticker)
     — SE falha: digest registra erro com causa → interrompe bloco mensal para este ativo

  5. tape_reflect_cycle — já chamado dentro de --modo orbit (run_orbit_update)
     — SE falha: digest registra erro → interrompe bloco mensal

  6. run_gate / run_backtest_gate(ticker)  [--modo backtest_gate]
     Detectar transição de status:
       status_antes = get_ativo(ticker)["status"]  # via delta_chaos_reader
       await run_backtest_gate(ticker)
       status_depois = get_ativo(ticker)["status"]
       SE status_antes != status_depois:
         emitir evento WebSocket "status_transition"
     — SE falha: digest registra erro com causa (mensagem do ValueError do gate.py)

  7. TUNE elegível?
     last_tune = max(c["data"] for c in dados["historico_config"] if "TUNE" in c["modulo"])
     dias_uteis = len(pd.bdate_range(last_tune, date.today()))
     SE dias_uteis >= 126:
       run_tune(ticker)
       digest registra resultado
     SE não: digest registra "TUNE — não elegível (N dias úteis)"
```

**Regra de dependência no bloco mensal:** falha em qualquer passo interrompe os passos seguintes para aquele ativo. Os demais ativos continuam.

**3.4 — Eventos WebSocket estruturados**

O orquestrador deve emitir eventos WebSocket estruturados (além dos logs de texto já existentes) para cada ativo processado:

```json
{
  "type": "orchestrator_ativo_result",
  "ticker": "VALE3",
  "ciclo_novo": true,
  "reflect_daily": "ok",
  "posicao": {
    "aberta": true,
    "pnl_atual": 0.85,
    "acao": "mantida"
  },
  "gate_eod": "OPERAR",
  "bloco_mensal": {
    "orbit": "ok",
    "reflect_cycle": "ok",
    "gate": "ok",
    "gate_resultado": "OPERAR",
    "status_anterior": "MONITORAR",
    "status_novo": "OPERAR",
    "tune": "pulado"
  },
  "erros": []
}
```

Se `status_anterior != status_novo`, emitir adicionalmente evento separado:

```json
{
  "type": "status_transition",
  "ticker": "VALE3",
  "status_anterior": "MONITORAR",
  "status_novo": "OPERAR",
  "ciclo": "2026-04"
}
```

**3.5 — Patch gate.py — registro de falha em historico_config[]**

Em `executar_gate(ticker)`, antes de lançar `ValueError` em qualquer ponto de falha (E0 cobertura mínima e E0 estratégias), registrar no master JSON:

```python
# Antes de: raise ValueError(...)
dados = tape_carregar_ativo(TICKER)
if "historico_config" not in dados:
    dados["historico_config"] = []
dados["historico_config"].append({
    "data":      str(datetime.now())[:10],
    "modulo":    "GATE v1.0",
    "parametro": "gate_decisao",
    "valor_novo": "FALHA",
    "motivo":    str(mensagem_de_erro),  # mensagem específica do ValueError
})
tape_salvar_ativo(TICKER, dados)
# raise ValueError(...) — mantém o raise
```

Aplicar nos dois pontos de falha que lançam ValueError:
- Falha E0 estratégias: `"estrategias nao configuradas no master JSON"`
- Falha E0 cobertura mínima: `"cobertura minima insuficiente (E0)"`

---

### BLOCO 4 — O que não deve ser tocado

- Lógica interna de `executar_gate()`, `executar_tune()`, `executar_orbit()` além do patch de registro
- `run_orbit()` em `dc_runner.py` — mantém comportamento atual, apontando para `--modo backtest_dados`
- `run_reflect()` existente em `dc_runner.py` — não modificar
- Fluxo de onboarding `/delta-chaos/onboarding` — sequência `backtest_dados → tune → backtest_gate` preservada
- Três books separados (`book_backtest`, `book_paper`, `book_live`) — invioláveis
- Escrita atômica (tempfile + os.replace) em todos os JSONs — obrigatória
- `gate_eod.py` — sem modificações
- `main.py` — sem modificações além de registrar novo endpoint se necessário

---

---

## PROMPT 2 — Frontend: digest por ativo + card de transição de status

---

### BLOCO 1 — Contexto do projeto

Sistema: ATLAS — frontend React  
Camada: frontend (`atlas_ui/src/`)  
Tecnologias relevantes: React, Zustand (`systemStore.js`), WebSocket (`useWebSocket.js`)  
Paleta CSS obrigatória — não alterar variáveis existentes em `tokens.css`

---

### BLOCO 2 — Situação atual

**2.1 — DigestPanel**

`atlas_ui/src/components/DigestPanel.jsx`

Recebe `items` como lista flat de objetos `{modulo, tipo, mensagem}`. Não há agrupamento por ativo. Não há tratamento de transição de status.

**2.2 — OrchestratorProgress**

`atlas_ui/src/components/OrchestratorProgress.jsx`

Tem 4 segmentos fixos hardcoded: TAPE, ORBIT, FIRE, GATE. Não reflete o novo fluxo.

**2.3 — systemStore.js**

`atlas_ui/src/store/systemStore.js`

`digestItems` é lista flat. Não há campo `ciclo_novo`, não há campo `status_transitions`, não há resultado por ativo.

**2.4 — TuneApprovalCard**

`atlas_ui/src/components/TuneApprovalCard.jsx`

Existe e funciona — serve de referência de padrão visual para o novo card de transição de status.

---

### BLOCO 3 — Comportamento desejado

**3.1 — systemStore.js — novos campos**

Adicionar ao estado:

```js
digestPorAtivo: {},      // { VALE3: { reflect_daily, gate_eod, posicao, bloco_mensal, erros }, ... }
cicloNovo: false,        // true quando bloco mensal rodou neste Check Status
statusTransitions: [],   // [{ ticker, status_anterior, status_novo, ciclo }]
```

Handler para novo evento WebSocket `orchestrator_ativo_result`:

```js
case "orchestrator_ativo_result":
  return {
    digestPorAtivo: {
      ...state.digestPorAtivo,
      [event.ticker]: event
    },
    cicloNovo: state.cicloNovo || event.ciclo_novo
  };

case "status_transition":
  return {
    statusTransitions: [...state.statusTransitions, event]
  };
```

Resetar `digestPorAtivo`, `cicloNovo`, `statusTransitions` em `orchestrator_start`.

**3.2 — DigestPanel — agrupado por ativo**

Modificar `DigestPanel.jsx` para receber `digestPorAtivo` (objeto) em vez de `items` (lista flat).

Layout por ativo:

```
VALE3                          ✓ ok
  reflect_daily   ✓
  gate_eod        ✓ OPERAR
  posição         P&L +0.85 — mantida

PETR4                          ⚠ alerta
  reflect_daily   ✓
  gate_eod        ~ MONITORAR

BOVA11                         ✗ erro
  orbit           ✗ sem dados OHLCV para 2026-04
```

Ícones por tipo (já definidos no contexto anterior):
- `✓` ok — `var(--atlas-green)`
- `⚠` alerta — `var(--atlas-amber)`
- `✗` erro/bloqueado — `var(--atlas-red)`
- `~` pendente — `var(--atlas-text-secondary)`

Transição MONITORAR→OPERAR dentro do digest do ativo: destaque em `var(--atlas-green)` com prefixo `↑ OPERAR` — visualmente distinto de um simples "ok".

**3.3 — OrchestratorProgress — segmentos dinâmicos**

Modificar `OrchestratorProgress.jsx` para receber `cicloNovo: bool` e `ativoAtual: string`.

SE `cicloNovo = false` — segmentos diários:
```
V0 | reflect_daily | posição/gate_eod | fim
```

SE `cicloNovo = true` — segmentos incluem bloco mensal:
```
V0 | reflect_daily | ORBIT | reflect_cycle | backtest_gate | TUNE? | posição/gate_eod | fim
```

O segmento ativo é destacado. Segmentos concluídos com `✓`. Segmentos com erro em `var(--atlas-red)`.

**3.4 — StatusTransitionCard — novo componente**

Criar `atlas_ui/src/components/StatusTransitionCard.jsx`.

Padrão visual: igual ao `TuneApprovalCard` — borda `var(--atlas-green)`, fundo `rgba(16,185,129,0.08)`.

Conteúdo:

```
↑ VALE3 — status atualizado (2026-04)
  Anterior: MONITORAR
  Novo:     OPERAR

[Confirmar]   [Revisar antes]
```

Botão "Confirmar": fecha o card, registra no digest como confirmado.  
Botão "Revisar antes": navega para aba Ativo → ORBIT do ticker.

Renderizado em `VisaoGeral.jsx` após `DigestPanel`, antes da tabela de ativos — mesmo padrão do `TuneApprovalCard`.

**3.5 — Integração em VisaoGeral.jsx**

Substituir passagem de `state.digestItems` por `state.digestPorAtivo` para o `DigestPanel`.  
Adicionar renderização de `StatusTransitionCard` para cada item em `state.statusTransitions` não confirmado.  
Passar `cicloNovo` e `ativoAtual` para `OrchestratorProgress`.

---

### BLOCO 4 — O que não deve ser tocado

- `tokens.css` — paleta CSS não deve ser alterada
- `TuneApprovalCard.jsx` — não modificar, apenas usar como referência visual
- `useWebSocket.js` — não modificar
- `AtivosTable.jsx`, `PosicoesTable.jsx` — sem modificações
- Abas internas (`AtivoView`, `ManutencaoView`) — sem modificações
- Lógica de `handleCheckStatus` em `VisaoGeral.jsx` além do que for necessário para passar novos campos ao store

---

*Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*  
*Spec v1.0 — sessão 2026-04-04*  
*Dois prompts separados: backend primeiro, frontend após SCAN do backend*
