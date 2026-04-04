// atlas_ui/src/App.jsx
import "./styles/tokens.css";
import { useCallback, useEffect, useState } from "react";
import CycleBar from "./components/CycleBar";
import ModeToggle from "./components/ModeToggle";
import HealthIndicator from "./components/HealthIndicator";
import MainScreen from "./layouts/MainScreen";
import FooterStatus from "./components/FooterStatus";
import RegimeAlert from "./components/RegimeAlert";
import OfflineBanner from "./components/OfflineBanner";
import { useSystemStore } from "./store/systemStore";
import { useAnalyticsStore } from "./store/analyticsStore";
import useWebSocket from "./hooks/useWebSocket";

const WS_BASE = "ws://localhost:8000";
const BACKEND_BASE = "http://localhost:8000";

export default function App() {
  const state = useSystemStore();
  const analytics = useAnalyticsStore();
  
  const [globalTab, setGlobalTab] = useState("delta_chaos");
  const [internalTab, setInternalTab] = useState("visao_geral");
  const [activeTicker, setActiveTicker] = useState("VALE3");
  const [isLoading, setIsLoading] = useState(false);

  const handleEvent = useCallback((event) => {
    state.updateFromEvent(event);
    analytics.update(event);
  }, []);

  useWebSocket(`${WS_BASE}/ws/events`, handleEvent);
  useWebSocket(`${WS_BASE}/ws/modules`, handleEvent);
  useWebSocket(`${WS_BASE}/ws/logs`, handleEvent);

  useEffect(() => {
    async function fetchAtivo() {
      if (globalTab !== "delta_chaos") return;
      
      setIsLoading(true);
      analytics.clear();
      
      try {
        const res = await fetch(`${BACKEND_BASE}/ativos/${activeTicker}`);
        if (!res.ok) throw new Error("Falha ao buscar ativo");
        const ativoData = await res.json();
        const ultimo = ativoData.historico?.slice(-1)[0] || {};
        
        state.updateFromEvent({
          type: "cycle_update",
          data: {
            ativo: activeTicker,
            regime: ultimo.regime || "DESCONHECIDO",
            regime_confianca: ultimo.score || 0,
            posicao: ultimo.sizing === 1 ? "ON" : "OFF",
            pnl: ultimo.ir || 0,
            cycle: ultimo.ciclo_id || "N/A",
          },
        });
      } catch (err) {
        console.warn("Erro ao carregar dados:", err.message);
      } finally {
        setIsLoading(false);
      }
    }
    
    fetchAtivo();
  }, [activeTicker, globalTab]);

  return (
    <div style={{ background: "var(--atlas-bg)", color: "var(--atlas-text-primary)", minHeight: "100vh" }}>
      
      {/* ✅ ADICIONAR ESTA LINHA */}
      <OfflineBanner />
      
      <RegimeAlert alert={state.alert} />
      <MainScreen 
        state={state} 
        analytics={analytics} 
        activeTicker={activeTicker} 
        onTickerChange={setActiveTicker} 
        isLoading={isLoading}
        globalTab={globalTab}
        setGlobalTab={setGlobalTab}
        internalTab={internalTab}
        setInternalTab={setInternalTab}
      />
      <FooterStatus staleness={analytics.staleness} />
    </div>
  );
}