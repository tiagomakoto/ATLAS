// atlas_ui/src/layouts/MainScreen.jsx
import React, { useState, useEffect, useMemo } from "react";
import CycleBar from "../components/CycleBar";
import ModeToggle from "../components/ModeToggle";
import HealthIndicator from "../components/HealthIndicator";
import ActionPanel from "../components/ActionPanel";
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

const API_BASE = "http://localhost:8000";

// === VIEWS INTERNAS ===
const VisaoGeral = ({ state, analytics, activeTicker, onTickerSelect, bookFonte, setBookFonte }) => {
  const [timeRange, setTimeRange] = useState("all");
  const [listaAtivos, setListaAtivos] = useState([]);
  const [book, setBook] = useState({ posicoes_abertas: [], pnl: 0, fonte: "paper" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const resAtivos = await fetch(`${API_BASE}/ativos`);
        if (!resAtivos.ok) throw new Error(`Erro HTTP: ${resAtivos.status}`);
        
        const dataAtivos = await resAtivos.json();
        const tickers = dataAtivos.ativos || [];
        
        if (tickers.length === 0) {
          setListaAtivos([]);
          setLoading(false);
          return;
        }
        
        const detalhes = await Promise.all(
          tickers.map(async (ticker) => {
            try {
              const res = await fetch(`${API_BASE}/ativos/${ticker}`);
              if (!res.ok) return null;
              const data = await res.json();
              return { ticker, ...data };
            } catch (err) {
              return null;
            }
          })
        );

        const ativosValidos = detalhes.filter(Boolean);
        setListaAtivos(ativosValidos);  // ✅ Salva no estado

        const resBook = await fetch(`${API_BASE}/ativos/book?fonte=${bookFonte}`);
        const dataBook = await resBook.json();
        setBook({ ...dataBook, fonte: bookFonte });
        
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [bookFonte]);

  const consolidado = useMemo(() => {
    const pnlTotal = book.pnl_total || 0;
    const deltaLiquido = book.delta_liquido || 0;
    const cobertura = book.cobertura_put_itm || 0;
    return { pnlTotal, deltaLiquido, cobertura };
  }, [book]);

  if (loading) return <div style={{ padding: 20, fontFamily: "monospace" }}>Carregando painéis...</div>;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <h4 style={{ fontFamily: "monospace", fontSize: 12, marginBottom: 8, color: "var(--atlas-text-primary)" }}>
        Ativos Parametrizados
      </h4>
      <AtivosTable ativos={listaAtivos} onSelect={onTickerSelect} />

      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
          <h4 style={{ fontFamily: "monospace", fontSize: 12, margin: 0, color: "var(--atlas-text-primary)" }}>
            Posições Abertas
          </h4>
          <select 
            value={bookFonte} 
            onChange={(e) => setBookFonte(e.target.value)}
            style={{
              background: "var(--atlas-surface)",
              border: "1px solid var(--atlas-border)",
              color: "var(--atlas-text-primary)",
              fontFamily: "monospace",
              fontSize: 10,
              padding: "4px 8px"
            }}
          >
            <option value="paper">🟡 PAPER</option>
            <option value="backtest">🔵 BACKTEST</option>
            <option value="live">🔴 LIVE</option>
          </select>
        </div>
        <PosicoesTable posicoes={book.posicoes_abertas} fonte={bookFonte} />
        <div style={{ marginTop: 8, padding: 8, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", fontFamily: "monospace", fontSize: 11 }}>
          <strong>Portfólio:</strong> Delta líquido: {consolidado.deltaLiquido.toFixed(2)} | Cobertura PUT ITM: {consolidado.cobertura}% | P&L total: <span style={{ color: consolidado.pnlTotal >= 0 ? "var(--atlas-green)" : "var(--atlas-red)" }}>{consolidado.pnlTotal.toFixed(2)}</span>
        </div>
      </section>

      <section>
        <h4 style={{ fontFamily: "monospace", fontSize: 12, marginBottom: 8 }}>Eventos Recentes</h4>
        <EventFeed events={state.events?.slice(0, 10) || []} />
      </section>
    </div>
  );
};

const ManutencaoView = () => (
  <div style={{ fontFamily: "monospace", fontSize: 11 }}>
    <h4 style={{ color: "var(--atlas-text-primary)", marginBottom: 12 }}>Manutenção</h4>
    <div style={{ marginBottom: 16 }}>
      <strong>Upload EOD</strong>
      <p style={{ color: "var(--atlas-text-secondary)", marginTop: 4 }}>Formatos aceitos: .csv, .parquet</p>
    </div>
    <div style={{ marginBottom: 16 }}>
      <strong>Upload Calendário de Eventos</strong>
      <p style={{ color: "var(--atlas-text-secondary)", marginTop: 4 }}>tipo_evento: earnings, dividendo, copom, vencimento_opcoes, rebalanceamento, macro</p>
    </div>
    <div>
      <strong>Versionamento de Config</strong>
      <p style={{ color: "var(--atlas-text-secondary)", marginTop: 4 }}>Histórico acessível via ConfigEditor (sem alteração de lógica)</p>
    </div>
  </div>
);

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

  const internalTabs = [
    { id: "visao_geral", label: "Visão Geral" },
    { id: "ativo", label: "Ativo" },
    { id: "manutencao", label: "Manutenção" },
  ];

  return (
    <div style={{ background: "var(--atlas-bg)", color: "var(--atlas-text-primary)", minHeight: "100vh" }}>
      
      {/* ✅ HEADER SEPARADO */}
      <Header state={state} cycleData={cycleData} mode={mode} />

      {/* ✅ NAV DE NAVEGAÇÃO GLOBAL COM TOOLTIPS + C02 */}
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
                    <div style={{ marginTop: 4 }}>
                      • Ativos parametrizados
                    </div>
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
                {/* ✅ C02: Badge `·` em vez de ⚠ */}
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
              {internalTab === "ativo" && <AtivoView activeTicker={activeTicker} analytics={analytics} />}
              {internalTab === "manutencao" && <ManutencaoView />}
            </>
          )}
        </main>

        {/* ✅ CORREÇÃO: ActionPanel APENAS na aba "Ativo" */}
        {globalTab === "delta_chaos" && internalTab === "ativo" && (
          <aside style={{ 
            width: 300, 
            borderLeft: "1px solid var(--atlas-border)", 
            padding: 20, 
            background: "var(--atlas-surface)",
            overflowY: "auto"
          }}>
            <ActionPanel activeTicker={activeTicker} onTickerChange={onTickerChange} />
          </aside>
        )}
      </div>
    </div>
  );
}