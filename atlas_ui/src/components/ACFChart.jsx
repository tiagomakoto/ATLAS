// atlas_ui/src/components/ACFChart.jsx
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, 
  CartesianGrid, ResponsiveContainer, ReferenceLine 
} from "recharts";

export default function ACFChart({ data }) {
  if (!data || !data.lags || !data.values) {
    return (
      <div style={{ 
        fontFamily: "monospace", 
        fontSize: 11, 
        color: "var(--atlas-text-secondary)", 
        padding: 20,
        textAlign: "center",
        background: "var(--atlas-surface)",
        border: "1px dashed var(--atlas-border)",
        borderRadius: 4
      }}>
        Aguardando dados de ACF...
      </div>
    );
  }

  const chartData = data.lags.map((lag, i) => ({
    lag,
    value: data.values[i] ?? 0
  }));

  const confidenceBand = data.confidence_band || 0;
  const n = data.n || 0;

  // ✅ B01: Calcular domínio Y DINÂMICO com margem de 20%
  const acfValues = chartData.map(d => d.value).filter(v => v !== null && v !== undefined);
  
  let yDomain = [-1, 1]; // Fallback
  
  if (acfValues.length > 0) {
    const minVal = Math.min(...acfValues);
    const maxVal = Math.max(...acfValues);
    const range = maxVal - minVal;
    const margin = range * 0.2; // 20% de margem
    
    // ✅ Garantir que zero sempre esteja visível
    yDomain = [
      Math.min(minVal - margin, 0),
      Math.max(maxVal + margin, 0)
    ];
  }

  return (
    <div style={{ 
      fontFamily: "monospace", 
      fontSize: 11,
      background: "var(--atlas-surface)",
      border: "1px solid var(--atlas-border)",
      borderRadius: 4,
      padding: 16
    }}>
      {/* Título */}
      <div style={{ 
        marginBottom: 12,
        color: "var(--atlas-text-primary)",
        fontWeight: "bold",
        fontSize: 12
      }}>
        Autocorrelação (ACF) — Lags 1 a 30
      </div>

      {/* Gráfico */}
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={chartData}>
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="var(--atlas-border)" 
            opacity={0.3} 
          />
          
          {/* Linhas de confiança */}
          <ReferenceLine 
            y={confidenceBand} 
            stroke="var(--atlas-amber)" 
            strokeDasharray="3 3" 
            opacity={0.6}
          />
          <ReferenceLine 
            y={-confidenceBand} 
            stroke="var(--atlas-amber)" 
            strokeDasharray="3 3" 
            opacity={0.6}
          />
          
          {/* Linha zero */}
          <ReferenceLine 
            y={0} 
            stroke="var(--atlas-text-secondary)" 
            opacity={0.5}
          />
          
          <XAxis 
            dataKey="lag" 
            tick={{ 
              fontSize: 9, 
              fontFamily: "monospace", 
              fill: "var(--atlas-text-secondary)" 
            }}
            tickLine={false}
            axisLine={{ stroke: "var(--atlas-border)" }}
            label={{ 
              value: "Lag", 
              position: "insideBottomRight", 
              offset: -5,
              fill: "var(--atlas-text-secondary)",
              fontSize: 9
            }}
          />
          
          {/* ✅ YAxis COM domínio dinâmico */}
          <YAxis 
            domain={yDomain}
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
              background: "var(--atlas-bg)",
              border: "1px solid var(--atlas-border)",
              borderRadius: 4,
              fontFamily: "monospace",
              fontSize: 10
            }}
            labelStyle={{ color: "var(--atlas-text-primary)", marginBottom: 4 }}
            formatter={(value, name) => {
              if (name === "value") return [value.toFixed(4), "ACF"];
              return [value, name];
            }}
            labelFormatter={(label) => `Lag ${label}`}
          />
          
          {/* Barras de ACF */}
          <Bar 
            dataKey="value" 
            fill="var(--atlas-blue)" 
            opacity={0.7}
            radius={[2, 2, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>

      {/* ✅ B01: NOTA EXPLICATIVA SOBRE SÉRIE COMPLETA */}
      <div style={{ 
        marginTop: 12,
        padding: "8px 12px",
        background: "rgba(59,130,246,0.1)",
        border: "1px solid var(--atlas-blue)",
        borderRadius: 2,
        fontFamily: "monospace",
        fontSize: 9,
        color: "var(--atlas-text-secondary)",
        lineHeight: 1.5
      }}>
        <div style={{ marginBottom: 4 }}>
          <strong style={{ color: "var(--atlas-blue)" }}>ACF calculada sobre série histórica completa</strong>
        </div>
        <div>
          N = {n} dias úteis • Bandas de confiança: ±{confidenceBand.toFixed(4)}
        </div>
        <div style={{ marginTop: 4, fontStyle: "italic" }}>
          * Janelas curtas produzem bandas de confiança estatisticamente instáveis.
        </div>
      </div>

      {/* Legenda */}
      <div style={{ 
        marginTop: 8,
        display: "flex", 
        gap: 16, 
        fontSize: 9,
        color: "var(--atlas-text-secondary)"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <div style={{ width: 12, height: 2, background: "var(--atlas-amber)" }} />
          <span>Limite 95% confiança</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <div style={{ width: 12, height: 2, background: "var(--atlas-blue)" }} />
          <span>ACF significativa (fora das bandas)</span>
        </div>
      </div>
    </div>
  );
}