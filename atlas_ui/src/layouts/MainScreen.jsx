// atlas_ui/src/layouts/MainScreen.jsx
import React, { useState, useEffect, useMemo } from "react";
import CycleBar from "../components/CycleBar";
import ModeToggle from "../components/ModeToggle";
import HealthIndicator from "../components/HealthIndicator";
import EventFeed from "../components/EventFeed";
import WalkForwardChart from "../components/WalkForwardChart";
import DistributionChart from "../components/DistributionChart";
import ACFChart from "../components/ACFChart";
import TailMetrics from "../components/TailMetrics";
import TimeRangeSelector from "../components/TimeRangeSelector";
import AtivosTable from "../components/AtivosTable";
import PosicoesTable from "../components/PosicoesTable";
import AtivoView from "../components/AtivoView";
import Tooltip from "../components/Tooltip";
import Header from "../components/Header";
import OrchestratorLogDrawer from "../components/OrchestratorLogDrawer";
import DigestPanel from "../components/DigestPanel";
import StatusTransitionCard from "../components/StatusTransitionCard";
import GestaoView from "../components/GestaoView";
import { useSystemStore } from "../store/systemStore";

const API_BASE = "http://localhost:8000";

// === VIEWS INTERNAS ===
// === COMPONENTE VISÃO GERAL (v2.5.2) ===
const VisaoGeral = ({ 
  state, activeTicker, onTickerSelect, bookFonte, setBookFonte 
}) => {
  const [listaAtivos, setListaAtivos] = useState([]);
  const [book, setBook] = useState({ posicoes_abertas: [] });
  const [ultimaRun, setUltimaRun] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const [drawerEventos, setDrawerEventos] = useState([]);  // ═══ NOVO: acumular eventos do DAILY
  const updateFromEvent = useSystemStore((s) => s.updateFromEvent);

  // ═══ NOVO: Callback para Drawer processar eventos da API (fallback) ═══
  const handleDrawerEvent = (event) => {
    // Passa evento para o Drawer processar (luzes + mensagens)
    // Mas também atualiza o Store para o ReadingPanel funcionar
    updateFromEvent(event);
    // ═══ NOVO: Adicionar evento à lista para passar via props ao Drawer ═══
    setDrawerEventos(prev => [...prev, event]);
  };
  
  // ═══ NOVO: Limpar drawerEventos quando inicia novo ciclo ═══
  useEffect(() => {
    if (state.dailyAtivo) {
      setDrawerEventos([]);
    }
  }, [state.dailyAtivo]);

  useEffect(() => { fetchData(); }, [bookFonte]);

  async function fetchData() {
    try {
      const resAtivos = await fetch(`${API_BASE}/ativos`);
      const dataAtivos = await resAtivos.json();
      const tickers = dataAtivos.ativos || [];

      const detalhes = await Promise.all(
        tickers.map(async (t) => {
          const r = await fetch(`${API_BASE}/ativos/${t}`);
          return r.ok ? { ticker: t, ...(await r.json()) } : null;
        })
      );
      const ativosFiltrados = detalhes.filter(Boolean);
      setListaAtivos(ativosFiltrados);
      
      // v2.7: Atualizar store com dados completos dos ativos
      updateFromEvent({ type: "ativos_parametrizados_loaded", data: ativosFiltrados });

      const resBook = await fetch(`${API_BASE}/ativos/book?fonte=${bookFonte}`);
      if (resBook.ok) setBook(await resBook.json());
    } catch (e) { console.error(e); }
  }

  async function handleCheckStatus() {
    setCarregando(true);
    updateFromEvent({ type: "daily_start" });
    // #3 FIX: Atualizar tabela de ativos no início do ciclo
    await fetchData();

    // ═══ NOVO: Pequeno delay para WebSocket do drawer conectar antes da API ═══
    await new Promise(resolve => setTimeout(resolve, 100));
    // ═══ FIM NOVO ═══

    try {
      const res = await fetch(`${API_BASE}/delta-chaos/daily/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: "manual" })
      });

      const data = await res.json();

      if (res.ok) {
        // v2.6 — processar eventos estruturados por ativo
        if (data.eventos && Array.isArray(data.eventos)) {
          for (const ev of data.eventos) {
            // ═══ NOVO: Passar evento para o Drawer via callback (fallback) ═══
            handleDrawerEvent(ev);
            // ═══ FIM NOVO ═══
            
            // Emitir status_transition se houver
            if (ev.bloco_mensal && ev.bloco_mensal.status_anterior !== ev.bloco_mensal.status_novo) {
              updateFromEvent({
                type: "status_transition",
                ticker: ev.ticker,
                status_anterior: ev.bloco_mensal.status_anterior,
                status_novo: ev.bloco_mensal.status_novo,
                ciclo: ev.bloco_mensal.ciclo || ""
              });
            }
          }
        }
        // Sinalizar conclusão — reseta dailyAtivo
        updateFromEvent({
          type: "daily_done",
          data: {
            items: [],
            timestamp: new Date().toISOString()
          }
        });
        // Fallback para formato antigo (v2.5.2)
        if (data.digest) {
          updateFromEvent({
            type: "daily_done",
            data: {
              items: data.digest,
              timestamp: new Date().toISOString()
            }
          });
        }
      } else {
        updateFromEvent({ type: "daily_error" });
      }

      setUltimaRun(new Date().toLocaleString("pt-BR"));
      await fetchData(); 
    } catch (e) { 
      console.error(e); 
      updateFromEvent({ type: "daily_error" });
    }
    finally { setCarregando(false); }
  }

  const rodando = carregando || state.dailyAtivo;

  const sectionLabel = {
    fontFamily: "monospace", fontSize: 9,
    color: "var(--atlas-text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.08em", marginBottom: 8
  };

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

      {/* BLOCO 1.5 — Log Drawer do Orquestrador */}
      <OrchestratorLogDrawer 
        isRunning={rodando} 
        isFinished={state.dailyConcluido}
        drawerEvents={drawerEventos}  // ═══ NOVO: passar eventos via props
      />

      {/* BLOCO 3 — Digest por ativo (após run) */}
      {(Object.keys(state.digestPorAtivo || {}).length > 0) && (
        <DigestPanel
          digestPorAtivo={state.digestPorAtivo}
          timestamp={state.digestTimestamp}
        />
      )}

      {/* BLOCO 3.5 — Status Transition Cards */}
      {(state.statusTransitions || []).map((tr, i) => (
        <StatusTransitionCard
          key={`${tr.ticker}-${i}`}
          ticker={tr.ticker}
          status_anterior={tr.status_anterior}
          status_novo={tr.status_novo}
          ciclo={tr.ciclo}
        />
      ))}

      {/* BLOCO 5 — Ativos Parametrizados */}
      <section>
        <div style={sectionLabel}>Ativos Parametrizados</div>
        <AtivosTable />
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
};

// === COMPONENTE PRINCIPAL ===
export default function MainScreen({ state, analytics, activeTicker, onTickerChange, isLoading, globalTab, setGlobalTab, internalTab, setInternalTab }) {
  const mode = state.mode || "observation";
  const cycleData = state.cycle;
  const [bookFonte, setBookFonte] = useState("paper");

  const globalTabs = [
    { id: "delta_chaos", label: "Delta Chaos", implemented: true },
    { id: "cripto", label: "Cripto", implemented: false },
    { id: "buy_hold", label: "Buy & Hold", implemented: false },
    { id: "trending", label: "Trending", implemented: false },
  ];

  // ✅ REMOVIDO "manutencao" — agora está dentro do AtivoView
  const internalTabs = [
    { id: "visao_geral", label: "Visão Geral" },
    { id: "ativo",       label: "Ativo" },
    { id: "gestao",      label: "Gestão" },
  ];

  return (
    <div style={{ background: "var(--atlas-bg)", color: "var(--atlas-text-primary)", minHeight: "100vh" }}>
      {/* HEADER SEPARADO */}
      <Header state={state} cycleData={cycleData} mode={mode} />

      {/* NAV DE NAVEGAÇÃO GLOBAL COM TOOLTIPS */}
      <nav style={{ display: "flex", borderBottom: "1px solid var(--atlas-border)", background: "var(--atlas-surface)" }}>
        {globalTabs.map((tab) => {
          const isPlaceholder = !tab.implemented;
          const isActive = globalTab === tab.id;

          return (
            <Tooltip
              key={tab.id}
              content={
                isPlaceholder ? (
                  <div style={{ lineHeight: 1.6 }}>
                    <div><strong>{tab.label.toUpperCase()}</strong></div>
                    <div style={{ marginTop: 4, color: "var(--atlas-amber)" }}>
                      Módulo previsto — não implementado nesta versão
                    </div>
                    <div style={{ marginTop: 4, fontSize: 9 }}>
                      Roadmap: v3.0+
                    </div>
                  </div>
                ) : (
                  <div style={{ lineHeight: 1.6 }}>
                    <div><strong>{tab.label.toUpperCase()}</strong></div>
                    <div style={{ marginTop: 4 }}>
                      Módulo ativo — visão completa do Delta Chaos
                    </div>
                    <div style={{ marginTop: 4 }}>• Ativos parametrizados</div>
                    <div>• Posições abertas</div>
                    <div>• Analytics em tempo real</div>
                  </div>
                )
              }
              position="bottom"
              delay={600}
            >
              <button
                onClick={() => {
                  if (isPlaceholder) return;
                  setGlobalTab(tab.id);
                }}
                style={{
                  padding: "10px 20px",
                  background: isActive ? "var(--atlas-bg)" : "transparent",
                  border: "none",
                  borderBottom: isActive 
                    ? "2px solid var(--atlas-blue)" 
                    : "2px solid transparent",
                  color: isActive 
                    ? "var(--atlas-text-primary)" 
                    : "var(--atlas-text-secondary)",
                  fontFamily: "monospace",
                  fontSize: 12,
                  cursor: isPlaceholder ? "default" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  textTransform: "uppercase"
                }}
              >
                {tab.label}
                {isPlaceholder && (
                  <span 
                    style={{ 
                      fontSize: 14, 
                      color: "var(--atlas-text-secondary)",
                      fontWeight: "bold"
                    }}
                  >
                    ·
                  </span>
                )}
              </button>
            </Tooltip>
          );
        })}
      </nav>

      <div className="main-content" style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <main className="scrollable-content" style={{ flex: 1, padding: 20, overflowY: "auto" }}>
          {globalTab !== "delta_chaos" ? (
            <div style={{ padding: 40, textAlign: "center", color: "var(--atlas-text-secondary)" }}>
              <h3>{globalTabs.find(t => t.id === globalTab)?.label}</h3>
              <p>Módulo previsto — não implementado nesta versão.</p>
            </div>
          ) : (
            <>
              <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
                {internalTabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setInternalTab(tab.id)}
                    style={{
                      padding: "6px 12px",
                      background: internalTab === tab.id ? "var(--atlas-blue)" : "var(--atlas-surface)",
                      border: "1px solid var(--atlas-border)",
                      color: internalTab === tab.id ? "#fff" : "var(--atlas-text-secondary)",
                      fontFamily: "monospace",
                      fontSize: 11,
                      borderRadius: 2,
                      cursor: "pointer"
                    }}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {internalTab === "visao_geral" && (
                <VisaoGeral 
                  state={state} 
                  analytics={analytics} 
                  activeTicker={activeTicker} 
                  onTickerSelect={onTickerChange}
                  bookFonte={bookFonte}
                  setBookFonte={setBookFonte}
                />
              )}

              {internalTab === "ativo" && (
                <AtivoView 
                  activeTicker={activeTicker} 
                  analytics={analytics}
                  onTickerChange={onTickerChange}
                />
              )}

              {internalTab === "gestao" && (
                <GestaoView />
              )}
            </>
          )}
        </main>

        {/* ✅ REMOVIDO: ActionPanel lateral */}
      </div>
    </div>
  );
}