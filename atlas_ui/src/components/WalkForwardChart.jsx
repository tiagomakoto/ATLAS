// atlas_ui/src/components/WalkForwardChart.jsx
import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from "recharts";

export default function WalkForwardChart({ data }) {
  const series = data?.walkForward?.series || data?.series || [];

  if (!series.length) {
    return (
      <div style={{
        fontFamily: "monospace",
        fontSize: 11,
        color: "var(--atlas-text-secondary)",
        padding: 20,
        textAlign: "center",
        background: "var(--atlas-bg)",
        border: "1px solid var(--atlas-border)",
        borderRadius: 4
      }}>
        Sem dados de Walk Forward
      </div>
    );
  }

  return (
    <div style={{
      background: "var(--atlas-bg)",
      border: "1px solid var(--atlas-border)",
      borderRadius: 4,
      padding: 16
    }}>
      <div style={{
        fontFamily: "monospace",
        fontSize: 10,
        color: "var(--atlas-text-secondary)",
        marginBottom: 12,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center"
      }}>
        WALK FORWARD ANALYSIS
        <span style={{ fontSize: 9, color: "var(--atlas-text-secondary)", fontStyle: "italic" }}>
          * Janela inicial excluída do backtest
        </span>
      </div>

      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={series}>
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="var(--atlas-border)" 
            opacity={0.5} 
          />
          
          {/* Linha threshold em y=0 */}
          <ReferenceLine 
            y={0} 
            stroke="var(--atlas-amber)" 
            strokeDasharray="4 4" 
            strokeWidth={2}
            label={{ 
              value: "ZERO", 
              position: "right", 
              fill: "var(--atlas-amber)",
              fontSize: 9,
              fontFamily: "monospace"
            }} 
          />
          
          {/* ✅ B02: Eixo X com ciclo_label se disponível, senão window_end */}
          <XAxis 
            dataKey={series[0]?.ciclo_label ? "ciclo_label" : "window_end"} 
            tick={{ 
              fontSize: 9, 
              fontFamily: "monospace", 
              fill: "var(--atlas-text-secondary)" 
            }}
            tickLine={false}
            axisLine={{ stroke: "var(--atlas-border)" }}
            interval="preserveStartEnd"
          />
          
          <YAxis 
            tick={{ 
              fontSize: 9, 
              fontFamily: "monospace", 
              fill: "var(--atlas-text-secondary)" 
            }}
            tickLine={false}
            axisLine={{ stroke: "var(--atlas-border)" }}
            tickFormatter={(value) => value.toFixed(2)}
          />
          
          <Tooltip
            contentStyle={{
              background: "var(--atlas-surface)",
              border: "1px solid var(--atlas-border)",
              borderRadius: 4,
              fontFamily: "monospace",
              fontSize: 10
            }}
            labelStyle={{ color: "var(--atlas-text-primary)", marginBottom: 4 }}
            itemStyle={{ color: "var(--atlas-blue)" }}
            formatter={(value, name) => {
              if (name === "ir_mean") return [value.toFixed(2), "IR Médio"];
              if (name === "ci_lower") return [value.toFixed(2), "IC Inferior"];
              if (name === "ci_upper") return [value.toFixed(2), "IC Superior"];
              return [value, name];
            }}
          />
          
          {/* Linha principal: ir_mean */}
          <Line 
            type="monotone" 
            dataKey="ir_mean" 
            stroke="var(--atlas-blue)" 
            strokeWidth={2} 
            dot={false}
            activeDot={{ 
              r: 6, 
              fill: "var(--atlas-blue)", 
              stroke: "var(--atlas-bg)", 
              strokeWidth: 2 
            }} 
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Legenda */}
      <div style={{ 
        display: "flex", 
        gap: 16, 
        marginTop: 12, 
        fontFamily: "monospace", 
        fontSize: 9 
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 12, height: 2, background: "var(--atlas-blue)" }} />
          <span style={{ color: "var(--atlas-text-secondary)" }}>IR Médio</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 12, height: 2, background: "var(--atlas-amber)" }} />
          <span style={{ color: "var(--atlas-text-secondary)" }}>Threshold Zero</span>
        </div>
      </div>
    </div>
  );
}