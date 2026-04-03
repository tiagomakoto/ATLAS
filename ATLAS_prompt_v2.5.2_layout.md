# ATLAS — Prompt v2.5.2: Layout Orquestrador + Manutenção Enxuta

**Versão:** 2.5.2
**Natureza:** Patch de layout — reposicionamento do Orquestrador,
remoção de botões individuais, Manutenção enxuta
**Base:** ATLAS v2.5.1
**Autorizado por:** CEO Tiago
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board

---

## 1. PROBLEMA DE LAYOUT ATUAL

A implementação atual tem:

- Aba **ORQUESTRADOR** dentro da seção "Ativo" (ao lado de ORBIT,
  REFLECT, CICLOS, ANALYTICS) — **errado conceitualmente**
- Botões **RUN GATE**, **RUN TUNE**, **RUN ORBIT**, **RUN EOD**
  visíveis na interface — **contradiz o modelo de dois pontos de contato**

O Orquestrador opera sobre todos os ativos simultaneamente.
Não pertence à análise de um ativo específico.

---

## 2. MODELO OPERACIONAL — DOIS PONTOS DE CONTATO

Os únicos pontos de contato do operador com o Delta Chaos via ATLAS são:

**A) Confirmar upload do arquivo EOD** — depositar o xlsx e clicar
"Check Status". O sistema faz o resto automaticamente.

**B) Onboarding de novo ativo** — declarar um ticker novo.
O sistema enfileira TAPE → ORBIT → TUNE → GATE automaticamente.

Mais um ponto de contato mínimo estratégico:

**C) Aprovar resultado do TUNE** — um clique quando novos parâmetros
chegam. Não é operacional.

**Não existem botões individuais de RUN GATE, RUN TUNE, RUN ORBIT,
RUN EOD na interface.** Operações de diagnóstico isoladas serão
implementadas na v2.6 via Terminal de comandos estruturados.

---

## 3. ESTRUTURA DE NAVEGAÇÃO CORRIGIDA

### 3.1 — Navegação global (abas superiores)

```
[ Delta Chaos ] [ Cripto · ] [ Buy & Hold · ] [ Trending · ]
```

Sem alteração nesta versão.

### 3.2 — Navegação interna Delta Chaos

```
[ Visão Geral ]  [ Ativo ]  [ Manutenção ]
```

**Remover** a aba "ORQUESTRADOR" de dentro de "Ativo".
O Orquestrador passa a viver **dentro da Visão Geral**.

### 3.3 — Sub-abas de "Ativo"

```
[ ORBIT ] [ REFLECT ] [ CICLOS ] [ ANALYTICS ]
```

Remover "ORQUESTRADOR" e "MANUTENÇÃO" daqui.
Manutenção já é aba de nível superior — não precisa repetir.

---

## 4. LAYOUT COMPLETO — VISÃO GERAL

Ordem vertical dos blocos:

```
┌─────────────────────────────────────────────────────────────┐
│ BLOCO 1 — Check Status                                      │
│ [● CHECK STATUS]                   última run: 03/04 07:42  │
├─────────────────────────────────────────────────────────────┤
│ BLOCO 2 — Progress (visível apenas quando rodando)          │
│ Tarefa 2/4: Verificando TUNE            ████████░░░  67%    │
│ ▬▬▬▬ ░░░░ ░░░░ ░░░░  (segmentos por tarefa)               │
├─────────────────────────────────────────────────────────────┤
│ BLOCO 3 — Digest (visível após run, persiste)               │
│ ✓ ORBIT    todos atualizados                                │
│ ~ TUNE     VALE3 aguarda aprovação                          │
│ ✓ GATE     todos válidos                                    │
│ ✓ EOD      executado — 1 posição aberta                     │
├─────────────────────────────────────────────────────────────┤
│ BLOCO 4 — Card aprovação TUNE (se houver)                   │
│ TUNE VALE3 — TP atual: 0.90 → sugerido: 0.75               │
│ IR atual: +0.389  IR sugerido: +0.412                       │
│ [Aplicar]   [Manter atual]                                  │
├─────────────────────────────────────────────────────────────┤
│ BLOCO 5 — Ativos Parametrizados                             │
│ tabela de ativos...                                         │
├─────────────────────────────────────────────────────────────┤
│ BLOCO 6 — Posições Abertas — PAPER                          │
│ tabela de posições...                                       │
└─────────────────────────────────────────────────────────────┘
```

**Não há seção de overrides manuais** na Visão Geral.
Operações de diagnóstico → v2.6 Terminal.

---

## 5. LAYOUT COMPLETO — MANUTENÇÃO

A Manutenção fica enxuta. Três seções apenas:

```
┌─────────────────────────────────────────────────────────────┐
│ ONBOARDING DE NOVO ATIVO                                    │
│ Ticker: [________] [Iniciar onboarding]                     │
│ O sistema roda: TAPE → ORBIT → TUNE → GATE automaticamente  │
├─────────────────────────────────────────────────────────────┤
│ EXPORTAR CONFIGURAÇÃO                                       │
│ [Exportar config JSON]  [Exportar relatório de sessão]      │
├─────────────────────────────────────────────────────────────┤
│ VERSIONAMENTO                                               │
│ Histórico de versões do config — sem alteração de lógica    │
└─────────────────────────────────────────────────────────────┘
```

**Remover da Manutenção:**
- Upload de arquivo xlsx — não é mais necessário como ação manual.
  O operador deposita o arquivo na pasta e clica Check Status.
- TP e Stop Loss manual — gerenciado pelo TUNE automaticamente.
  O card de aprovação do TUNE na Visão Geral substitui essa função.

---

## 6. IMPLEMENTAÇÃO — FRONTEND

### 6.1 — `MainScreen.jsx` — remover aba Orquestrador de `internalTabs`

```javascript
// Substituir:
const internalTabs = [
  { id: "visao_geral", label: "Visão Geral" },
  { id: "ativo",       label: "Ativo" },
  { id: "manutencao",  label: "Manutenção" },
];

// As sub-abas de Ativo ficam:
const ativoSubTabs = [
  { id: "orbit",     label: "ORBIT" },
  { id: "reflect",   label: "REFLECT" },
  { id: "ciclos",    label: "CICLOS" },
  { id: "analytics", label: "ANALYTICS" },
  // ORQUESTRADOR e MANUTENÇÃO removidos daqui
];
```

### 6.2 — `VisaoGeral` — componente completo

```jsx
// Substituir o componente VisaoGeral atual integralmente

import { useState, useEffect } from "react";
import AtivosTable from "../components/AtivosTable";
import PosicoesTable from "../components/PosicoesTable";
import OrchestratorProgress from "../components/OrchestratorProgress";
import DigestPanel from "../components/DigestPanel";
import TuneApprovalCard from "../components/TuneApprovalCard";

const API_BASE = "http://localhost:8000";

export default function VisaoGeral({
  state, activeTicker, onTickerSelect, bookFonte, setBookFonte
}) {
  const [listaAtivos,  setListaAtivos]  = useState([]);
  const [book,         setBook]         = useState({ posicoes_abertas: [] });
  const [ultimaRun,    setUltimaRun]    = useState(null);
  const [carregando,   setCarregando]   = useState(false);

  useEffect(() => { fetchData(); }, [bookFonte]);

  async function fetchData() {
    try {
      const resAtivos = await fetch(`${API_BASE}/ativos`);
      const { ativos: tickers } = await resAtivos.json();

      const detalhes = await Promise.all(
        tickers.map(async (t) => {
          const r = await fetch(`${API_BASE}/ativos/${t}`);
          return r.ok ? { ticker: t, ...(await r.json()) } : null;
        })
      );
      setListaAtivos(detalhes.filter(Boolean));

      const resBook = await fetch(
        `${API_BASE}/ativos/book?fonte=${bookFonte}`);
      if (resBook.ok) setBook(await resBook.json());
    } catch (e) { console.error(e); }
  }

  async function handleCheckStatus() {
    setCarregando(true);
    try {
      await fetch(`${API_BASE}/orchestrator/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: "manual" })
      });
      setUltimaRun(new Date().toLocaleString("pt-BR"));
      await fetchData(); // atualiza tabelas após run
    } catch (e) { console.error(e); }
    finally { setCarregando(false); }
  }

  async function handleAplicarTune(ticker, tp, stop) {
    await fetch(`${API_BASE}/ativos/${ticker}/update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        data: { take_profit: tp, stop_loss: stop },
        description: `TUNE aplicado — TP=${tp} STOP=${stop}`,
        confirm: true
      })
    });
    await fetchData();
  }

  const rodando = carregando || state.orchestratorAtivo;

  // Extrai tickers com TUNE pendente do digest
  const tunesPendentes = (state.digestItems || [])
    .filter(i => i.tipo === "aprovacao_pendente" && i.modulo === "TUNE")
    .map(i => i.ticker)
    .filter(Boolean);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

      {/* BLOCO 1 — Check Status */}
      <div style={{
        display: "flex", alignItems: "center",
        justifyContent: "space-between",
        padding: "10px 14px",
        background: "var(--atlas-surface)",
        border: "1px solid var(--atlas-border)",
        borderRadius: 2
      }}>
        <button
          onClick={handleCheckStatus}
          disabled={rodando}
          style={{
            padding: "8px 20px",
            background: rodando ? "var(--atlas-border)" : "var(--atlas-blue)",
            border: "none",
            color: rodando ? "var(--atlas-text-secondary)" : "#fff",
            fontFamily: "monospace", fontSize: 11,
            borderRadius: 2,
            cursor: rodando ? "not-allowed" : "pointer",
            letterSpacing: 1, textTransform: "uppercase"
          }}
        >
          {rodando ? "● Verificando..." : "Check Status"}
        </button>

        {ultimaRun && (
          <span style={{
            fontFamily: "monospace", fontSize: 9,
            color: "var(--atlas-text-secondary)"
          }}>
            última verificação: {ultimaRun}
          </span>
        )}
      </div>

      {/* BLOCO 2 — Progress (só quando rodando) */}
      {state.orchestratorAtivo && state.progresso && (
        <OrchestratorProgress progresso={state.progresso} />
      )}

      {/* BLOCO 3 — Digest (após run) */}
      {(state.digestItems?.length > 0) && (
        <DigestPanel
          items={state.digestItems}
          timestamp={state.digestTimestamp}
        />
      )}

      {/* BLOCO 4 — Cards de aprovação TUNE */}
      {tunesPendentes.map(ticker => (
        <TuneApprovalCard
          key={ticker}
          ticker={ticker}
          onAplicar={handleAplicarTune}
        />
      ))}

      {/* BLOCO 5 — Ativos Parametrizados */}
      <section>
        <div style={sectionLabel}>Ativos Parametrizados</div>
        <AtivosTable ativos={listaAtivos} onSelect={onTickerSelect} />
      </section>

      {/* BLOCO 6 — Posições Abertas */}
      <section>
        <div style={{
          display: "flex", justifyContent: "space-between",
          alignItems: "center", marginBottom: 8
        }}>
          <div style={sectionLabel}>Posições Abertas</div>
          <select
            value={bookFonte}
            onChange={e => setBookFonte(e.target.value)}
            style={{
              background: "var(--atlas-surface)",
              border: "1px solid var(--atlas-border)",
              color: "var(--atlas-text-primary)",
              fontFamily: "monospace", fontSize: 10,
              padding: "3px 8px"
            }}
          >
            <option value="paper">🟡 PAPER</option>
            <option value="live">🔴 LIVE</option>
          </select>
        </div>
        <PosicoesTable
          posicoes={book.posicoes_abertas}
          fonte={bookFonte}
        />
      </section>
    </div>
  );
}

const sectionLabel = {
  fontFamily: "monospace", fontSize: 9,
  color: "var(--atlas-text-secondary)",
  textTransform: "uppercase",
  letterSpacing: "0.08em", marginBottom: 8
};
```

### 6.3 — Novo componente `DigestPanel.jsx`

```jsx
// atlas_ui/src/components/DigestPanel.jsx

export default function DigestPanel({ items, timestamp }) {
  if (!items?.length) return null;

  const icone = (tipo) => ({
    ok:                  "✓",
    alerta:              "⚠",
    bloqueado:           "✗",
    aprovacao_pendente:  "~",
    info:                "·"
  }[tipo] || "·");

  const cor = (tipo) => ({
    ok:                  "var(--atlas-green)",
    alerta:              "var(--atlas-red)",
    bloqueado:           "var(--atlas-red)",
    aprovacao_pendente:  "var(--atlas-amber)",
    info:                "var(--atlas-text-secondary)"
  }[tipo] || "var(--atlas-text-secondary)");

  return (
    <div style={{
      padding: 12,
      background: "var(--atlas-surface)",
      border: "1px solid var(--atlas-border)",
      borderRadius: 2,
      fontFamily: "monospace", fontSize: 10
    }}>
      <div style={{
        color: "var(--atlas-text-secondary)",
        textTransform: "uppercase",
        letterSpacing: 1, marginBottom: 10, fontSize: 9
      }}>
        Check Status — {timestamp
          ? new Date(timestamp).toLocaleString("pt-BR")
          : "—"}
      </div>

      {items.map((item, i) => (
        <div key={i} style={{
          display: "flex", gap: 12,
          padding: "3px 0",
          borderBottom: i < items.length - 1
            ? "1px solid var(--atlas-border)"
            : "none"
        }}>
          <span style={{ color: cor(item.tipo), width: 10 }}>
            {icone(item.tipo)}
          </span>
          <span style={{
            color: "var(--atlas-text-primary)",
            width: 60, flexShrink: 0
          }}>
            {item.modulo}
          </span>
          <span style={{ color: "var(--atlas-text-secondary)" }}>
            {item.mensagem}
          </span>
        </div>
      ))}
    </div>
  );
}
```

### 6.4 — Novo componente `TuneApprovalCard.jsx`

```jsx
// atlas_ui/src/components/TuneApprovalCard.jsx
import { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";

export default function TuneApprovalCard({ ticker, onAplicar }) {
  const [dados, setDados] = useState(null);

  useEffect(() => {
    async function fetchTune() {
      const res = await fetch(`${API_BASE}/ativos/${ticker}`);
      if (!res.ok) return;
      const data = await res.json();

      const tunes = (data.historico_config || [])
        .filter(c => c.modulo?.includes("TUNE"))
        .sort((a, b) => b.data.localeCompare(a.data));

      if (!tunes.length) return;
      const ultimo = tunes[0];

      // Extrai TP e STOP do valor_novo (formato: "TP=0.75 STOP=1.5")
      const match = ultimo.valor_novo?.match(
        /TP=([\d.]+)\s+STOP=([\d.]+)/);
      if (!match) return;

      setDados({
        ticker,
        tpAtual:    data.take_profit,
        stopAtual:  data.stop_loss,
        tpSugerido: parseFloat(match[1]),
        stopSugerido: parseFloat(match[2]),
        irAtual:    null,   // disponível no futuro via analytics
        irSugerido: null,
        data:       ultimo.data
      });
    }
    fetchTune();
  }, [ticker]);

  if (!dados) return null;

  return (
    <div style={{
      padding: 14,
      background: "rgba(245,158,11,0.08)",
      border: "1px solid var(--atlas-amber)",
      borderRadius: 2,
      fontFamily: "monospace", fontSize: 11
    }}>
      <div style={{
        color: "var(--atlas-amber)", fontSize: 9,
        textTransform: "uppercase", letterSpacing: 1,
        marginBottom: 10
      }}>
        TUNE {dados.ticker} — resultado disponível ({dados.data})
      </div>

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(2, 1fr)",
        gap: 8, marginBottom: 12
      }}>
        <div style={{
          padding: 8, background: "var(--atlas-surface)",
          borderRadius: 2
        }}>
          <div style={{ fontSize: 9,
                        color: "var(--atlas-text-secondary)",
                        marginBottom: 4 }}>
            Parâmetros atuais
          </div>
          <div>TP: <strong>{dados.tpAtual}</strong></div>
          <div>STOP: <strong>{dados.stopAtual}x</strong></div>
        </div>
        <div style={{
          padding: 8,
          background: "rgba(245,158,11,0.1)",
          borderRadius: 2
        }}>
          <div style={{ fontSize: 9,
                        color: "var(--atlas-amber)",
                        marginBottom: 4 }}>
            Parâmetros sugeridos
          </div>
          <div>TP: <strong>{dados.tpSugerido}</strong></div>
          <div>STOP: <strong>{dados.stopSugerido}x</strong></div>
        </div>
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <button
          onClick={() => onAplicar(
            dados.ticker, dados.tpSugerido, dados.stopSugerido)}
          style={{
            padding: "6px 16px",
            background: "var(--atlas-green)",
            border: "none", color: "#fff",
            fontFamily: "monospace", fontSize: 10,
            borderRadius: 2, cursor: "pointer",
            textTransform: "uppercase"
          }}
        >
          Aplicar
        </button>
        <button
          onClick={() => setDados(null)}
          style={{
            padding: "6px 16px",
            background: "var(--atlas-surface)",
            border: "1px solid var(--atlas-border)",
            color: "var(--atlas-text-secondary)",
            fontFamily: "monospace", fontSize: 10,
            borderRadius: 2, cursor: "pointer",
            textTransform: "uppercase"
          }}
        >
          Manter atual
        </button>
      </div>
    </div>
  );
}
```

### 6.5 — `ManutencaoView` — versão enxuta

```jsx
// Substituir ManutencaoView atual

import { useState } from "react";

const API_BASE = "http://localhost:8000";

export default function ManutencaoView() {
  const [novoAtivo, setNovoAtivo] = useState("");
  const [onboarding, setOnboarding] = useState(false);
  const [onboardingMsg, setOnboardingMsg] = useState("");

  async function handleOnboarding() {
    if (!novoAtivo.trim()) return;
    setOnboarding(true);
    setOnboardingMsg("");
    try {
      const res = await fetch(`${API_BASE}/delta-chaos/onboarding`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: novoAtivo.trim().toUpperCase(),
          confirm: true,
          description: `Onboarding ${novoAtivo.trim().toUpperCase()}`
        })
      });
      const data = await res.json();
      setOnboardingMsg(
        res.ok
          ? `✓ ${novoAtivo.toUpperCase()} — onboarding iniciado`
          : `✗ ${data.detail}`
      );
    } catch (e) {
      setOnboardingMsg(`✗ Erro: ${e.message}`);
    } finally {
      setOnboarding(false);
      setNovoAtivo("");
    }
  }

  async function exportarConfig() {
    const res = await fetch(`${API_BASE}/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ state: {}, analytics: {}, staleness: 0 })
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `atlas_config_${new Date().toISOString().slice(0,10)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const labelStyle = {
    fontFamily: "monospace", fontSize: 9,
    color: "var(--atlas-text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.08em", marginBottom: 8, display: "block"
  };

  const sectionStyle = {
    padding: 14,
    background: "var(--atlas-surface)",
    border: "1px solid var(--atlas-border)",
    borderRadius: 2
  };

  return (
    <div style={{
      display: "flex", flexDirection: "column", gap: 16,
      maxWidth: 480
    }}>

      {/* Onboarding novo ativo */}
      <div style={sectionStyle}>
        <span style={labelStyle}>Onboarding de novo ativo</span>
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <input
            value={novoAtivo}
            onChange={e => setNovoAtivo(e.target.value.toUpperCase())}
            placeholder="Ex: WEGE3"
            maxLength={6}
            style={{
              flex: 1, padding: "6px 10px",
              background: "var(--atlas-bg)",
              border: "1px solid var(--atlas-border)",
              color: "var(--atlas-text-primary)",
              fontFamily: "monospace", fontSize: 11,
              borderRadius: 2,
              textTransform: "uppercase"
            }}
          />
          <button
            onClick={handleOnboarding}
            disabled={!novoAtivo.trim() || onboarding}
            style={{
              padding: "6px 14px",
              background: (!novoAtivo.trim() || onboarding)
                ? "var(--atlas-border)"
                : "var(--atlas-blue)",
              border: "none", color: "#fff",
              fontFamily: "monospace", fontSize: 10,
              borderRadius: 2, cursor: "pointer",
              textTransform: "uppercase"
            }}
          >
            {onboarding ? "..." : "Iniciar"}
          </button>
        </div>
        {onboardingMsg && (
          <div style={{
            fontFamily: "monospace", fontSize: 10,
            color: onboardingMsg.startsWith("✓")
              ? "var(--atlas-green)"
              : "var(--atlas-red)"
          }}>
            {onboardingMsg}
          </div>
        )}
        <div style={{
          marginTop: 8, fontFamily: "monospace", fontSize: 9,
          color: "var(--atlas-text-secondary)"
        }}>
          Sequência automática: TAPE → ORBIT → TUNE → GATE
        </div>
      </div>

      {/* Exportar */}
      <div style={sectionStyle}>
        <span style={labelStyle}>Exportar</span>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={exportarConfig}
            style={{
              padding: "6px 14px",
              background: "var(--atlas-surface)",
              border: "1px solid var(--atlas-border)",
              color: "var(--atlas-text-secondary)",
              fontFamily: "monospace", fontSize: 10,
              borderRadius: 2, cursor: "pointer",
              textTransform: "uppercase"
            }}
          >
            Relatório de sessão
          </button>
        </div>
      </div>

    </div>
  );
}
```

---

## 7. ENDPOINT NOVO — Onboarding

Adicionar em `atlas_backend/api/routes/delta_chaos.py`:

```python
class OnboardingPayload(BaseModel):
    ticker: str
    confirm: bool = False
    description: str = ""

@router.post("/onboarding")
async def onboarding(payload: OnboardingPayload):
    """
    Inicia onboarding completo de novo ativo.
    Sequência: TAPE → ORBIT → TUNE → GATE
    Cada etapa roda em sequência via dc_runner.
    """
    _validar_confirm(payload.confirm, payload.description)
    ticker = payload.ticker.strip().upper()

    # Valida formato do ticker (4-6 caracteres alfanuméricos)
    import re
    if not re.match(r"^[A-Z0-9]{4,6}$", ticker):
        raise HTTPException(
            status_code=400,
            detail=f"Ticker inválido: {ticker}"
        )

    try:
        from core.dc_runner import run_orbit, run_tune, run_gate
        from core.terminal_stream import emit_log

        emit_log(f"[ONBOARDING] Iniciando {ticker}", level="info")

        # ORBIT
        await run_orbit(ticker=ticker,
                        anos=list(range(2002, 2026)))
        # TUNE
        await run_tune(ticker=ticker)
        # GATE
        await run_gate(ticker=ticker)

        emit_log(f"[ONBOARDING] {ticker} concluído", level="info")
        return {"status": "OK", "ticker": ticker}

    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 8. DEFINIÇÃO DE PRONTO

- [ ] Aba ORQUESTRADOR removida das sub-abas de Ativo
- [ ] Sub-abas de Ativo: apenas ORBIT, REFLECT, CICLOS, ANALYTICS
- [ ] Botões RUN GATE, RUN TUNE, RUN ORBIT, RUN EOD removidos da interface
- [ ] `VisaoGeral` com os seis blocos na ordem especificada
- [ ] Bloco 2 (Progress) visível apenas quando orquestrador está ativo
- [ ] Bloco 3 (Digest) visível após run, persiste até próximo Check Status
- [ ] Bloco 4 (TuneApprovalCard) visível quando há TUNE pendente
- [ ] `ManutencaoView` enxuta: onboarding + exportar apenas
- [ ] TP e Stop Loss removidos da Manutenção
- [ ] Upload xlsx removido da Manutenção
- [ ] Endpoint `POST /delta-chaos/onboarding` implementado
- [ ] `DigestPanel.jsx` criado
- [ ] `TuneApprovalCard.jsx` criado

**Critério de rejeição imediato:** qualquer botão de RUN individual
visível na interface normal, ou TP/Stop Loss editável diretamente
sem passar pelo fluxo TUNE.

---

## 9. ROADMAP — v2.6 TERMINAL DE COMANDOS

*Especificação completa na v2.6. Registrado aqui como decisão de arquitetura.*

### Estrutura

Nova aba **Terminal** na navegação global, ao lado de "TRENDING":

```
[ Delta Chaos ] [ Cripto · ] [ Buy & Hold · ] [ Trending · ] [ Terminal ]
```

### Modelo de comando

```
init {sistema} {comando} {argumento}

Exemplos:
  init delta_chaos gate VALE3
  init delta_chaos orbit PETR4
  init delta_chaos tune BOVA11
  init delta_chaos status
  init cripto status          ← futuro
```

### Constraints obrigatórios (v2.6)

- **Sandboxed:** não expõe shell. Não aceita `cd`, `ls`, `python`,
  nenhum comando de sistema operacional
- **Dicionário de comandos por sistema:** cada sistema registra
  seus comandos válidos. Comandos desconhecidos retornam erro explícito
- **Output estruturado:** JSON para dados de diagnóstico,
  MD para relatórios, texto para logs
- **Autenticação de comando:** todo comando passa por validação
  de argumento (ticker deve estar na lista de ativos conhecidos)

*Implementação na v2.6 após v2.5.2 aprovada pelo SCAN.*

---

*Prompt redigido por Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*
*Sessão: off-ata | Autorização: CEO Tiago*
*Base: ATLAS v2.5.1*
*Contribuições: Douglas (conceito dois pontos de contato),
Livermore (layout Visão Geral), Müller (override via Terminal v2.6),
Taleb (sandbox Terminal)*
