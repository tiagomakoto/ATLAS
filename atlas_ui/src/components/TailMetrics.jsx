// atlas_ui/src/components/TailMetrics.jsx
import React from "react";

export default function TailMetrics({ data }) {
  // ✅ C05: Aceitar ambos formatos (snake_case e camelCase)
  const skew = data?.skew ?? data?.skewness ?? null;
  const kurtosis = data?.kurtosis ?? null;
  const p1 = data?.p1 ?? data?.percentile_1 ?? null;
  const p99 = data?.p99 ?? data?.percentile_99 ?? null;

  if (!skew && !kurtosis) {
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
        Sem dados de Fat Tails
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
        marginBottom: 12 
      }}>
        TAIL METRICS
      </div>
      
      <div style={{ 
        display: "grid", 
        gridTemplateColumns: "repeat(2, 1fr)", 
        gap: 12 
      }}>
        {/* Skew */}
        <div style={{ padding: 8, background: "var(--atlas-surface)", borderRadius: 2 }}>
          <div style={{ fontSize: 8, color: "var(--atlas-text-secondary)", marginBottom: 4 }}>
            SKEW
          </div>
          <div style={{ 
            fontSize: 14, 
            fontFamily: "monospace", 
            fontWeight: "bold",
            color: skew !== null ? (skew > 0.5 ? "var(--atlas-amber)" : "var(--atlas-text-primary)") : "var(--atlas-text-secondary)"
          }}>
            {skew !== null ? skew.toFixed(3) : "—"}
          </div>
        </div>

        {/* Kurtosis */}
        <div style={{ padding: 8, background: "var(--atlas-surface)", borderRadius: 2 }}>
          <div style={{ fontSize: 8, color: "var(--atlas-text-secondary)", marginBottom: 4 }}>
            KURTOSIS
          </div>
          <div style={{ 
            fontSize: 14, 
            fontFamily: "monospace", 
            fontWeight: "bold",
            color: kurtosis !== null ? (kurtosis > 3 ? "var(--atlas-amber)" : "var(--atlas-text-primary)") : "var(--atlas-text-secondary)"
          }}>
            {kurtosis !== null ? kurtosis.toFixed(3) : "—"}
          </div>
        </div>

        {/* ✅ C05: P1% (percentil 1) */}
        <div style={{ padding: 8, background: "var(--atlas-surface)", borderRadius: 2 }}>
          <div style={{ fontSize: 8, color: "var(--atlas-text-secondary)", marginBottom: 4 }}>
            P1%
          </div>
          <div style={{ 
            fontSize: 14, 
            fontFamily: "monospace", 
            fontWeight: "bold",
            color: p1 !== null ? "var(--atlas-red)" : "var(--atlas-text-secondary)"
          }}>
            {p1 !== null ? p1.toFixed(3) : "—"}
          </div>
        </div>

        {/* ✅ C05: P99% (percentil 99) */}
        <div style={{ padding: 8, background: "var(--atlas-surface)", borderRadius: 2 }}>
          <div style={{ fontSize: 8, color: "var(--atlas-text-secondary)", marginBottom: 4 }}>
            P99%
          </div>
          <div style={{ 
            fontSize: 14, 
            fontFamily: "monospace", 
            fontWeight: "bold",
            color: p99 !== null ? "var(--atlas-green)" : "var(--atlas-text-secondary)"
          }}>
            {p99 !== null ? p99.toFixed(3) : "—"}
          </div>
        </div>
      </div>

      {/* Legenda */}
      <div style={{ 
        marginTop: 12, 
        fontSize: 9, 
        color: "var(--atlas-text-secondary)", 
        fontFamily: "monospace",
        lineHeight: 1.4
      }}>
        <div>• P1%: Pior cenário (1% dos casos)</div>
        <div>• P99%: Melhor cenário (99% dos casos)</div>
      </div>
    </div>
  );
}