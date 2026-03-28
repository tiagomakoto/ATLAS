import HealthIndicator from "../components/HealthIndicator";
import ModuleGrid from "../components/ModuleGrid";
import CycleBar from "../components/CycleBar";
import EventFeed from "../components/EventFeed";
import WalkForwardChart from "../components/WalkForwardChart";
import DistributionChart from "../components/DistributionChart";
import ACFChart from "../components/ACFChart";
import TailMetrics from "../components/TailMetrics";
import TimeRangeSelector from "../components/TimeRangeSelector";
import { useState, useMemo } from "react";

export default function ReadingPanel({ state, analytics, activeTicker }) {
  const [timeRange, setTimeRange] = useState("all");

  const filteredWalkForward = useMemo(() => {
    if (!analytics?.walkForward?.series) return analytics?.walkForward;
    const { series, ...rest } = analytics.walkForward;
    if (timeRange === "all") return analytics.walkForward;
    const cutoffs = { current: 1, "30d": 1, "6m": 6 };
    const n = cutoffs[timeRange] || series.length;
    return { ...rest, series: series.slice(-n) };
  }, [analytics?.walkForward, timeRange]);

  return (
    <div style={{ border: "1px solid var(--atlas-border)", padding: 10, overflowY: "auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <h3 style={{ fontFamily: "monospace", fontSize: 14, margin: 0 }}>{activeTicker}</h3>
        <HealthIndicator status={state.health} />
      </div>
      
      <div style={{ marginTop: 8 }}>
        <CycleBar cycle={state.cycle} />
      </div>
      
      <div style={{ marginTop: 8, fontFamily: "monospace", fontSize: 11 }}>
        <div><strong>Regime:</strong> {state.cycle?.regime || "—"}</div>
        <div><strong>Estratégia:</strong> {state.cycle?.estrategia || "—"}</div>
        <div><strong>Anos Válidos:</strong> {state.cycle?.anos_validos || "—"}</div>
        <div><strong>Confiança:</strong> {state.cycle?.regime_confianca ? (state.cycle.regime_confianca * 100).toFixed(1) + "%" : "—"}</div>
      </div>

      <div style={{ marginTop: 8 }}>
        <ModuleGrid modules={state.modules} />
      </div>

      <div style={{ marginTop: 8 }}>
        <EventFeed events={state.events} />
      </div>

      <div style={{ marginTop: 12, borderTop: "1px solid var(--atlas-border)", paddingTop: 8 }}>
        <TimeRangeSelector value={timeRange} onChange={setTimeRange} />
        {filteredWalkForward && <WalkForwardChart data={filteredWalkForward} />}
        <DistributionChart data={analytics.distribution} />
        <ACFChart data={analytics.acf} />
        <TailMetrics data={analytics.fatTails} />
      </div>
    </div>
  );
}