# SPEC — Drawer de Onboarding por Ativo
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board
**Data:** 2026-04-13
**Versão:** 1.0
**Modo:** Especificação — nova funcionalidade

---

## BLOCO 1 — Contexto do projeto

Sistema: ATLAS — frontend React + backend FastAPI + Delta Chaos via subprocess
Camada: Frontend (`atlas_ui/src/components/GestaoView.jsx`), backend (`atlas_backend/`), e `delta_chaos/tune.py`
Tecnologias relevantes: React, Zustand, FastAPI, WebSocket (`useWebSocket.js`), SQLite (Optuna), `dc_runner.py`
Regra inviolável: Delta Chaos nunca é importado diretamente — sempre via subprocess `dc_runner.py`

---

## BLOCO 2 — Situação atual

**Frontend:**
- `atlas_ui/src/components/GestaoView.jsx` — aba Gestão existente com seção "ONBOARDING DE NOVO ATIVO" contendo apenas um campo de texto (ticker) e botão INICIAR
- Não há drawer, não há steps, não há estado por etapa
- Ativos exibidos como linhas N/A com botões TUNE sem dados reais

**Backend:**
- `dc_runner.py` — possui `run_tune(ticker)` mas não possui funções para `backtest_dados` nem `backtest_gate`
- Não existe endpoint dedicado para onboarding sequencial
- Não existe persistência de estado de onboarding por ativo

**Delta Chaos:**
- `tune.py` — `executar_tune()` usa Optuna com persistência SQLite em `TMP_DIR/tune_{TICKER}.db` (patch já aplicado)
- `tune.py` — NÃO emite `emit_event` por trial — WebSocket fica silencioso durante execução
- `edge.py` — modos CLI disponíveis: `backtest_dados`, `tune`, `backtest_gate`
- Sequência canônica de onboarding: `backtest_dados` → `tune` → `backtest_gate`

**Estado de onboarding:**
- Não existe campo `onboarding_step` nem `onboarding_status` no master JSON dos ativos
- Não existe reconciliação de processo morto
- Não existe watchdog de processo silencioso

---

## BLOCO 3 — Comportamento desejado

### 3.1 — Estado persistido no master JSON

Adicionar ao master JSON de cada ativo (`ATIVOS_DIR/{TICKER}.json`) os seguintes campos ao iniciar onboarding:

```json
{
  "onboarding": {
    "step_atual": 1,
    "steps": {
      "1_backtest_dados": { "status": "idle", "iniciado_em": null, "concluido_em": null, "erro": null },
      "2_tune":           { "status": "idle", "iniciado_em": null, "concluido_em": null, "erro": null, "trials_completos": 0, "trials_total": 200 },
      "3_backtest_gate":  { "status": "idle", "iniciado_em": null, "concluido_em": null, "erro": null }
    },
    "ultimo_evento_em": null
  }
}
```

Status válidos por step: `idle` | `running` | `done` | `error` | `paused`

**Regra de reconciliação (watchdog):** Se `status == "running"` e `ultimo_evento_em` tem mais de 10 minutos, o backend promove automaticamente para `paused` na próxima leitura do endpoint. Esta operação deve ser idempotente.

**Regra de retomada:** Se `status == "paused"` no step 2 (tune), o processo retoma do trial persistido no SQLite — não reinicia do zero. O campo `trials_completos` é atualizado a cada evento de trial recebido.

**Estado inicial canônico:** Ativo recém-criado sem onboarding tem todos os steps em `idle` e `step_atual = 1`.

**Estado final canônico:** Onboarding completo tem todos os steps em `done` e `step_atual = 4` (sentinel de conclusão).

### 3.2 — Patch em tune.py — emit_event por trial

Adicionar chamada `emit_event` dentro do callback `_early_stop_cb` de `executar_tune()`, após a atualização de `_melhor_valor`:

```python
def _early_stop_cb(study, trial):
    if trial.number < OPTUNA_STARTUP:
        return
    if study.best_value > _melhor_valor[0] + OPTUNA_MIN_DELTA:
        _melhor_valor[0] = study.best_value
        _sem_melhoria[0] = 0
    else:
        _sem_melhoria[0] += 1
    # NOVO — emite evento por trial para WebSocket
    emit_event("TUNE", "trial", 
               trial_number=trial.number + 1,
               trials_total=OPTUNA_N_TRIALS,
               best_ir=round(_melhor_valor[0], 4),
               sem_melhoria=_sem_melhoria[0])
    if _sem_melhoria[0] >= OPTUNA_PATIENCE:
        study.stop()
```

Este patch é condição necessária para a barra de progresso funcionar. Sem ele, o WebSocket fica silencioso durante horas.

### 3.3 — Endpoint backend

Criar em `atlas_backend/api/routes/delta_chaos.py`:

**POST /delta-chaos/onboarding/iniciar**
```python
# Payload: { "ticker": "VALE3" }
# Ação: cria/atualiza campo onboarding no master JSON, dispara step 1 via subprocess
# Retorna: { "status": "started", "step": 1 }
```

**GET /delta-chaos/onboarding/{ticker}**
```python
# Retorna estado atual do onboarding do ativo
# Inclui reconciliação watchdog: se running + ultimo_evento_em > 10min → paused
# Retorna: campo onboarding completo do master JSON
```

**POST /delta-chaos/onboarding/{ticker}/retomar**
```python
# Retoma onboarding do step atual (usado quando status == "paused")
# Para step 2: Optuna continua do SQLite existente
# Retorna: { "status": "resumed", "step": N }
```

**GET /delta-chaos/onboarding/{ticker}/progresso-tune**
```python
# Lê tune_{TICKER}.db via conexão read-only
# Retorna: { "trials_completos": N, "trials_total": 200, "best_ir": X }
# Conexão deve ser read-only explícita para evitar conflito com processo de escrita
```

### 3.4 — Drawer de onboarding (frontend)

O botão INICIAR na seção de onboarding abre um drawer lateral (não modal — não bloqueia a tela inteira).

**Estrutura visual do drawer:**

```
┌─────────────────────────────────────┐
│ ONBOARDING — VALE3              [×] │
├─────────────────────────────────────┤
│ ● Step 1: backtest_dados       DONE │
│   Concluído em 2026-04-13 22:01     │
├─────────────────────────────────────┤
│ ⟳ Step 2: tune              RUNNING │
│   ████████░░░░░░░░  80 / 200 trials │
│   Melhor IR: +1.234                 │
│   Tempo médio/trial: 1.8s           │
│   Tempo decorrido: 2m 24s           │
│   Estimativa restante: ~4min        │
├─────────────────────────────────────┤
│ ○ Step 3: backtest_gate        IDLE │
└─────────────────────────────────────┘
```

**Estados visuais por step:**
- `idle` → ○ cinza, label "PENDENTE"
- `running` → ⟳ azul animado, label "EXECUTANDO"
- `done` → ● verde, label "CONCLUÍDO", data/hora de conclusão
- `error` → ✗ vermelho, label "ERRO", mensagem de erro
- `paused` → ⏸ âmbar, label "PAUSADO", botão [Retomar] visível

**Barra de progresso do TUNE:**
- Só aparece no step 2 quando `status == "running"` ou `status == "paused"`
- Atualizada via eventos WebSocket (`modulo == "TUNE"`, `status == "trial"`)
- Campos exibidos:
  - `trials_completos / trials_total`
  - Melhor IR atual (`best_ir`)
  - Tempo médio por trial (calculado: tempo_decorrido / trials_completos)
  - Tempo decorrido do ciclo atual (contador local desde `iniciado_em`)
  - Estimativa restante (tempo_médio × trials_restantes)

**Watchdog visual:**
- Se `status == "running"` e não recebe evento WebSocket de TUNE por mais de 5 minutos, exibe banner âmbar: "Processo sem sinal há Xmin — verifique o terminal"
- Não altera estado automaticamente no frontend — apenas alerta

**Transição para OPERAR:**
- Após step 3 concluído (`done`), exibe card de confirmação:
  "VALE3 aprovado pelo GATE — confirmar entrada em OPERAR?"
  Botões: [Confirmar entrada] [Manter em MONITORAR]
- Confirmação gera entrada em `historico_config[]` e atualiza status do ativo

### 3.5 — Lógica sequencial bloqueante

- Step 2 só é iniciado automaticamente após step 1 `done`
- Step 3 só é iniciado automaticamente após step 2 `done`
- Se qualquer step termina em `error`, a sequência para. O drawer exibe o erro e um botão [Reiniciar step] para aquele step específico
- Reiniciar step 2 com SQLite existente = retomada (não reinício)
- Reiniciar step 2 sem SQLite = reinício do zero (Optuna cria novo estudo)

---

## BLOCO 4 — O que não deve ser tocado

- `useWebSocket.js` — apenas consumir eventos, não modificar a interface
- `gate_eod.py`, `gate.py` — sem modificações
- `AtivosTable.jsx`, `PosicoesTable.jsx` — sem modificações
- `TuneApprovalCard.jsx` — sem modificações
- Lógica interna de `executar_tune()` além do patch de `emit_event` descrito em 3.2
- Escrita atômica (`tempfile + os.replace`) em todos os JSONs — obrigatória
- CLI `python -m delta_chaos.edge --modo tune --ticker VALE3` deve continuar funcionando independente do ATLAS
- Os três books (`book_backtest`, `book_paper`, `book_live`) — invioláveis

---

*Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*
*Spec v1.0 — 2026-04-13*
