// atlas_ui/src/components/Versionamento.jsx
import React, { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";

export default function Versionamento({ ticker }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ticker) return;
    
    async function fetchHistory() {
      try {
        const res = await fetch(`${API_BASE}/ativos/${ticker}`);
        if (!res.ok) throw new Error(`Erro HTTP: ${res.status}`);
        
        const data = await res.json();
        
        // ✅ Extrair historico_config do JSON do ativo
        const configHistory = data.historico_config || [];
        setHistory(configHistory);
      } catch (err) {
        console.error("Erro ao carregar histórico:", err);
      } finally {
        setLoading(false);
      }
    }
    
    fetchHistory();
  }, [ticker]);

  if (loading) {
    return <div style={{ padding: 20, color: "var(--atlas-text-secondary)" }}>Carregando...</div>;
  }

  return (
    <div style={{
      border: "1px solid var(--atlas-border)",
      borderRadius: 4,
      padding: 16,
      background: "var(--atlas-bg)"
    }}>
      <div style={{
        fontFamily: "monospace",
        fontSize: 10,
        color: "var(--atlas-text-secondary)",
        textTransform: "uppercase",
        letterSpacing: "0.08em",
        marginBottom: 12
      }}>
        Histórico de Versões
      </div>
      
      {history.length === 0 ? (
        <div style={{
          padding: 20,
          textAlign: "center",
          color: "var(--atlas-text-secondary)",
          fontFamily: "monospace",
          fontSize: 10
        }}>
          Nenhuma versão registrada
        </div>
      ) : (
        <div style={{ maxHeight: 400, overflowY: "auto" }}>
          {history.map((version, i) => (
            <div
              key={i}
              style={{
                padding: "8px 12px",
                background: "var(--atlas-surface)",
                border: "1px solid var(--atlas-border)",
                borderRadius: 4,
                marginBottom: 8,
                fontFamily: "monospace",
                fontSize: 9
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ color: "var(--atlas-text-primary)", fontWeight: "bold" }}>
                  {version.modulo || "Config"} — {version.data || i + 1}
                </span>
                <span style={{ color: "var(--atlas-text-secondary)" }}>
                  {version.data || "—"}
                </span>
              </div>
              <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>
                {version.parametro || "Parâmetro"}: {version.valor_novo || "—"}
              </div>
              <div style={{ color: "var(--atlas-text-secondary)", fontSize: 8, fontStyle: "italic" }}>
                {version.motivo || "Sem descrição"}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}