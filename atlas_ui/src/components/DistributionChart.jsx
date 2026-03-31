// atlas_ui/src/components/DistributionChart.jsx
import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from "recharts";

export default function DistributionChart({ data }) {
  const histogram = data?.histogram || [];
  const bins = data?.bins || [];
  const n = data?.n || 0;

  if (!histogram.length || !bins.length) {
    return (
      <div style={{
        fontFamily: "monospace",
        fontSize: 11,
        color: "var(--atlas-text-secondary)",
        padding: 40,
        textAlign: "center",
        background: "var(--atlas-bg)",
        border: "1px dashed var(--atlas-border)",
        borderRadius: 4
      }}>
        Aguardando dados de distribuição...
      </div>
    );
  }

  // ✅ Preparar dados para o gráfico
  const chartData = histogram.map((count, i) => {
    const binStart = bins[i]?.toFixed(4) || 0;
    const binEnd = bins[i + 1]?.toFixed(4) || 0;
    return {
      bin: `${binStart} a ${binEnd}`,
      count,
      binStart: parseFloat(binStart),
      binEnd: parseFloat(binEnd)
    };
  }).filter(d => d.count > 0); // Remover bins vazios

  // ✅ Calcular domínio Y com margem de 20%
  const maxCount = Math.max(...histogram);
  const yDomain = [0, Math.ceil(maxCount * 1.2)];

  return (
    <div style={{
      background: "var(--atlas-bg)",
      border: "1px solid var(--atlas-border)",
      borderRadius: 4,
      padding: 16,
      height: "100%",
      display: "flex",
      flexDirection: "column"
    }}>
      {/* Header */}
      <div style={{
        fontFamily: "monospace",
        fontSize: 10,
        color: "var(--atlas-text-secondary)",
        marginBottom: 16,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center"
      }}>
        <div>
          <div style={{ fontWeight: "bold", color: "var(--atlas-text-primary)", marginBottom: 4 }}>
            DISTRIBUIÇÃO DE RETORNOS
          </div>
          <div style={{ fontSize: 9 }}>
            N = {n} dias úteis
          </div>
        </div>
      </div>

      {/* ✅ Gráfico CENTRALIZADO com altura aumentada */}
      <div style={{
        flex: 1,
        minHeight: 300,
        width: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center"
      }}>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="var(--atlas-border)" 
              opacity={0.3} 
            />
            
            {/* Linha zero */}
            <ReferenceLine 
              y={0} 
              stroke="var(--atlas-text-secondary)" 
              opacity={0.5}
            />
            
            <XAxis 
              dataKey="bin"
              tick={{ 
                fontSize: 8, 
                fontFamily: "monospace", 
                fill: "var(--atlas-text-secondary)" 
              }}
              tickLine={false}
              axisLine={{ stroke: "var(--atlas-border)" }}
              interval="preserveStartEnd"
              angle={-45}
              textAnchor="end"
              height={60}
            />
            
            <YAxis 
              domain={yDomain}
              tick={{ 
                fontSize: 9, 
                fontFamily: "monospace", 
                fill: "var(--atlas-text-secondary)" 
              }}
              tickLine={false}
              axisLine={{ stroke: "var(--atlas-border)" }}
              width={40}
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
              formatter={(value, name, props) => {
                if (name === "count") {
                  const percentage = n > 0 ? ((value / n) * 100).toFixed(1) : 0;
                  return [`${value} (${percentage}%)`, "Frequência"];
                }
                return [value, name];
              }}
              labelFormatter={(label) => `Retorno: ${label}`}
            />
            
            {/* ✅ Barras do histograma CENTRALIZADAS */}
            <Bar 
              dataKey="count" 
              fill="var(--atlas-blue)" 
              opacity={0.85}
              radius={[2, 2, 0, 0]}
              maxBarSize={40}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legenda */}
      <div style={{ 
        marginTop: 12,
        padding: "8px 12px",
        background: "var(--atlas-surface)",
        border: "1px solid var(--atlas-border)",
        borderRadius: 4,
        fontSize: 9,
        display: "flex",
        gap: 16,
        justifyContent: "center"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 12, height: 12, background: "var(--atlas-blue)", opacity: 0.85, borderRadius: 2 }} />
          <span style={{ color: "var(--atlas-text-secondary)" }}>Frequência de retornos</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ color: "var(--atlas-text-secondary)" }}>Eixo X: faixa de retorno diário</span>
        </div>
      </div>
    </div>
  );
}