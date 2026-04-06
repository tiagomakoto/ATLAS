# SPEC CIRÚRGICA — Delimitação de Camadas: dc_runner / delta_chaos.py / edge.py
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board  
**Data:** 2026-04-06  
**Versão:** 1.0  
**Modo:** Cirúrgico — correção arquitetural  
**Contexto:** SPEC_ATLAS_v2.6 foi implementada com sobreposição de responsabilidades identificada em teste de campo

---

## 1. Problema identificado

`orchestrator_run()` em `atlas_backend/api/routes/delta_chaos.py` contém lógica de sequenciamento, iteração de ativos, verificação de staleness e chamadas diretas a `get_ativo()` e `list_ativos()`. Isso viola a separação de camadas e duplica lógica que pertence ao `dc_runner.py`.

Consequência: dois orquestradores divergentes para o mesmo sistema, bugs que aparecem em um contexto e não no outro.

---

## 2. Separação de responsabilidades — definição canônica

```
edge.py          FAZ o trabalho — modos atômicos, autossuficientes
dc_runner.py     APERTA o botão — protocolo ATLAS↔Delta Chaos
delta_chaos.py   EXPÕE o botão — endpoints HTTP apenas
```

### edge.py — executor atômico

**Responsabilidade:** executar cada modo de forma completa e autossuficiente. Cada modo entra, executa, imprime resultado, sai. Não sabe nada sobre ATLAS, WebSocket ou sequenciamento.

**Regra:** nenhuma lógica de decisão sobre "quando rodar" ou "o que rodar a seguir". Só "como rodar este modo".

**Modos válidos (resultado desta sessão):**

| Modo | O que faz |
|---|---|
| `--modo orbit` | OHLCV cache + ORBIT skip-ciclo + tape_reflect_cycle |
| `--modo backtest_dados` | COTAHIST + ORBIT completo — onboarding only |
| `--modo backtest_gate` | backtest completo + 8 etapas GATE |
| `--modo tune` | calibração TP/STOP |
| `--modo eod` | paper/live diário completo |
| `--modo eod_preview` | preview sem executar |
| `--modo reflect_daily` | tape_process_eod_file para um ativo |
| `--modo gate_eod` | guarda leve diária |

### dc_runner.py — protocolo

**Responsabilidade:** saber **qual modo apertar**, **quando** e **em que ordem**. Capturar resultados. Emitir eventos WebSocket estruturados. Conter toda lógica de sequenciamento e decisão do orquestrador.

**Regra:** nunca implementa o que os modos fazem — só os chama via `_stream_subprocess()`. Toda lógica de "ciclo mudou?", "xlsx presente?", "posição aberta?" mora aqui.

**Funções que devem existir:**

```python
# Modos atômicos — um subprocess por função
run_orbit_update(ticker, anos)       # --modo orbit
run_backtest_gate(ticker)            # --modo backtest_gate  
run_tune(ticker)                     # --modo tune
run_eod(xlsx_dir)                    # --modo eod
run_eod_preview(xlsx_dir)            # --modo eod_preview
run_reflect_daily(ticker, xlsx_path) # --modo reflect_daily
run_gate_eod(ticker)                 # --modo gate_eod
run_orbit(ticker, anos)              # --modo backtest_dados (onboarding)
run_gate(ticker)                     # alias de run_backtest_gate

# Orquestrador — lógica de sequência completa
run_orchestrator(tickers)            # sequencia todos os modos
```

**`run_orchestrator()` — lógica de sequência:**

```python
async def run_orchestrator(tickers: list) -> dict:
    digest = {}
    for ticker in tickers:

        # [DIÁRIO]
        # 1. verificar dados disponíveis
        dados_ok = await _verificar_dados(ticker, ano, mes)
        
        # 2. reflect_daily se xlsx presente
        xlsx_path = _detectar_xlsx(ticker)
        if xlsx_path:
            await run_reflect_daily(ticker, xlsx_path)

        # 3. posição aberta?
        posicao = _ler_posicao_aberta(ticker)
        if posicao:
            resultado = _verificar_tp_stop(ticker, posicao, xlsx_path)
            if resultado["fechar"]:
                # sinaliza fechamento no digest — CEO executa
                digest[ticker] = {"acao": "fechar", **resultado}
                continue
            else:
                digest[ticker] = {"acao": "manter", "pnl": resultado["pnl"]}
                continue

        # 4. gate_eod
        parecer = await run_gate_eod(ticker)
        if parecer != "OPERAR":
            digest[ticker] = {"gate_eod": parecer}
            continue

        # [MENSAL — se ciclo mudou]
        if _ciclo_mudou(ticker):
            if not dados_ok["cotahist"]:
                digest[ticker] = {"bloco_mensal": "postergado — COTAHIST indisponível"}
                continue

            # 5. orbit
            result_orbit = await run_orbit_update(ticker)
            if result_orbit["status"] != "OK":
                digest[ticker] = {"orbit": "erro", "motivo": result_orbit["output"]}
                continue

            # 6. backtest_gate
            status_antes = _ler_status(ticker)
            result_gate = await run_backtest_gate(ticker)
            if result_gate["status"] != "OK":
                digest[ticker] = {"gate": "erro", "motivo": result_gate["output"]}
                continue
            status_depois = _ler_status(ticker)
            if status_antes != status_depois:
                _emitir_status_transition(ticker, status_antes, status_depois)

            # 7. tune se elegível
            if _tune_elegivel(ticker):
                await run_tune(ticker)

        digest[ticker] = {"status": "ok"}

    return digest
```

**Helpers privados que devem existir em `dc_runner.py`:**

```python
_detectar_xlsx(ticker) -> str | None
    # os.path.join(OPCOES_HOJE_DIR, f"{ticker}.xlsx")
    # retorna path se existe, None se não

_ciclo_mudou(ticker) -> bool
    # lê OHLCV cache: df.index.max().strftime("%Y-%m")
    # compara com historico[-1]["ciclo_id"] do master JSON

_ler_posicao_aberta(ticker) -> dict | None
    # lê book_paper.json
    # retorna ops onde data_saida == null e ativo == ticker

_verificar_tp_stop(ticker, posicao, xlsx_path) -> dict
    # lê preço atual do xlsx
    # calcula pnl_pct vs take_profit e stop_loss do master JSON
    # retorna {"fechar": bool, "motivo": str, "pnl": float}

_ler_status(ticker) -> str
    # chama get_ativo(ticker)["status"] via delta_chaos_reader

_tune_elegivel(ticker) -> bool
    # lê historico_config[], filtra TUNE, pega último
    # pd.bdate_range(last_tune_date, date.today()) >= 126

_verificar_dados(ticker, ano, mes) -> dict
    # chama tape_verificar_dados() para cotahist, selic, ohlcv
    # retorna {"cotahist": bool, "selic": bool, "ohlcv": bool}

_emitir_status_transition(ticker, antes, depois)
    # emite evento WebSocket estruturado tipo "status_transition"
```

### delta_chaos.py — router HTTP

**Responsabilidade:** expor endpoints. Receber payload HTTP. Chamar `dc_runner`. Retornar resultado. Nada mais.

**Regra:** zero lógica de negócio. Zero importações do Delta Chaos. Zero iteração de ativos. Zero verificação de staleness.

**Como deve ficar `orchestrator_run()`:**

```python
@router.post("/orchestrator/run")
async def orchestrator_run(payload: dict):
    tickers = list_ativos()
    result = await dc_runner.run_orchestrator(tickers)
    return {"status": "OK", "digest": result}
```

Quatro linhas. Sem mais.

---

## 3. O que remover de delta_chaos.py

Remover integralmente de `orchestrator_run()` em `delta_chaos.py`:

- Importações de `get_ativo`, `list_ativos` dentro da função
- Loop `for ticker in ativos`
- Lógica de verificação de staleness (`precisa_orbit`, `precisa_reflect`)
- Chamadas diretas a `run_orbit()`, `run_reflect()`
- Construção de `itens_digest` e `manutencao_realizada`
- Qualquer lógica condicional sobre dados ou ciclos

Tudo isso move para `run_orchestrator()` em `dc_runner.py`.

---

## 4. O que não deve ser tocado

- Assinatura dos endpoints existentes em `delta_chaos.py` — URLs e métodos HTTP mantidos
- `_stream_subprocess()` em `dc_runner.py` — não modificar
- Lógica interna de cada modo em `edge.py` — não modificar
- `delta_chaos_reader.py` — não modificar
- Três books separados — invioláveis
- Escrita atômica — obrigatória em qualquer novo JSON write

---

## 5. Definição de pronto

- `orchestrator_run()` em `delta_chaos.py` tem no máximo 5 linhas
- Toda lógica de sequência está em `run_orchestrator()` em `dc_runner.py`
- `edge.py` não contém nenhuma referência a ATLAS, WebSocket ou `book_paper.json`
- `dc_runner.py` não reimplementa o que os modos do `edge.py` fazem
- Check Status via ATLAS e CLI via `edge.py` produzem resultados equivalentes para o mesmo ticker

---

## 6. Relação com outras specs

- **SPEC_ATLAS_v2.6** — esta spec corrige a sobreposição arquitetural da implementação existente. O fluxo de `run_orchestrator()` aqui descrito substitui o `orchestrator_run()` da v2.6.
- **SPEC_TAPE_verificar_dados** — `_verificar_dados()` em `dc_runner.py` chama `tape_verificar_dados()` via subprocess ou import direto do reader — a ser decidido pelo Plan.
- **SPEC_ORBIT_skip_ciclo** — `run_orbit_update()` depende do comportamento de skip implementado nesta spec.

---

*Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*  
*Spec Cirúrgica v1.0 — 2026-04-06*  
*Correção arquitetural da SPEC_ATLAS_v2.6 — aplicar sobre código existente*
