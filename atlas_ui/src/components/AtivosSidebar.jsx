// atlas_ui/src/components/AtivosSidebar.jsx
import React, { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";

export default function AtivosSidebar({ activeTicker, onTickerChange }) {
  const [ativos, setAtivos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAtivos() {
      try {
        const res = await fetch(`${API_BASE}/ativos`);
        const data = await res.json();
        setAtivos(data.ativos || []);
      } catch (err) {
        console.error("Erro ao carregar ativos:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchAtivos();
  }, []);

  return (
    <aside style={{
      width: 250,
      borderRight: "1px solid var(--atlas-border)",
      padding: 16,
      background: "var(--atlas-surface)",
      overflowY: "auto"
    }}>
      <div style={{
        fontFamily: "monospace",
        fontSize: 10,
        color: "var(--atlas-text-secondary)",
        textTransform: "uppercase",
        letterSpacing: "0.08em",
        marginBottom: 12
      }}>
        Ativos
      </div>

      {loading ? (
        <div style={{
          padding: 20,
          textAlign: "center",
          color: "var(--atlas-text-secondary)",
          fontFamily: "monospace",
          fontSize: 9
        }}>
          Carregando...
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {ativos.map((ticker) => (
            <button
              key={ticker}
              onClick={() => onTickerChange(ticker)}
              style={{
                padding: "8px 12px",
                background: activeTicker === ticker ? "var(--atlas-blue)" : "var(--atlas-bg)",
                border: "1px solid var(--atlas-border)",
                color: activeTicker === ticker ? "#fff" : "var(--atlas-text-primary)",
                fontFamily: "monospace",
                fontSize: 10,
                borderRadius: 2,
                cursor: "pointer",
                textAlign: "left",
                textTransform: "uppercase"
              }}
            >
              {ticker}
            </button>
          ))}
        </div>
      )}
    </aside>
  );
}