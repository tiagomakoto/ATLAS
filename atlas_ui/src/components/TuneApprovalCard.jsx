import { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";

export default function TuneApprovalCard({ ticker, onAplicar }) {
  const [dados, setDados] = useState(null);

  useEffect(() => {
    async function fetchTune() {
      const res = await fetch(`${API_BASE}/ativos/${ticker}`);
      if (!res.ok) return;
      const data = await res.json();

      const tunes = (data.historico_config || [])
        .filter(c => c.modulo?.includes("TUNE"))
        .sort((a, b) => b.data.localeCompare(a.data));

      if (!tunes.length) return;
      const ultimo = tunes[0];

      const match = ultimo.valor_novo?.match(
        /TP=([\d.]+)\s+STOP=([\d.]+)/);
      if (!match) return;

      setDados({
        ticker,
        tpAtual:    data.take_profit,
        stopAtual:  data.stop_loss,
        tpSugerido: parseFloat(match[1]),
        stopSugerido: parseFloat(match[2]),
        irAtual:    null,
        irSugerido: null,
        data:       ultimo.data
      });
    }
    fetchTune();
  }, [ticker]);

  if (!dados) return null;

  return (
    <div style={{
      padding: 14,
      background: "rgba(245,158,11,0.08)",
      border: "1px solid var(--atlas-amber)",
      borderRadius: 2,
      fontFamily: "monospace", fontSize: 11
    }}>
      <div style={{
        color: "var(--atlas-amber)", fontSize: 9,
        textTransform: "uppercase", letterSpacing: 1,
        marginBottom: 10
      }}>
        TUNE {dados.ticker} — resultado disponível ({dados.data})
      </div>

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(2, 1fr)",
        gap: 8, marginBottom: 12
      }}>
        <div style={{
          padding: 8, background: "var(--atlas-surface)",
          borderRadius: 2
        }}>
          <div style={{ fontSize: 9,
                        color: "var(--atlas-text-secondary)",
                        marginBottom: 4 }}>
            Parâmetros atuais
          </div>
          <div>TP: <strong>{dados.tpAtual}</strong></div>
          <div>STOP: <strong>{dados.stopAtual}x</strong></div>
        </div>
        <div style={{
          padding: 8,
          background: "rgba(245,158,11,0.1)",
          borderRadius: 2
        }}>
          <div style={{ fontSize: 9,
                        color: "var(--atlas-amber)",
                        marginBottom: 4 }}>
            Parâmetros sugeridos
          </div>
          <div>TP: <strong>{dados.tpSugerido}</strong></div>
          <div>STOP: <strong>{dados.stopSugerido}x</strong></div>
        </div>
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <button
          onClick={() => onAplicar(
            dados.ticker, dados.tpSugerido, dados.stopSugerido)}
          style={{
            padding: "6px 16px",
            background: "var(--atlas-green)",
            border: "none", color: "#fff",
            fontFamily: "monospace", fontSize: 10,
            borderRadius: 2, cursor: "pointer",
            textTransform: "uppercase"
          }}
        >
          Aplicar
        </button>
        <button
          onClick={() => setDados(null)}
          style={{
            padding: "6px 16px",
            background: "var(--atlas-surface)",
            border: "1px solid var(--atlas-border)",
            color: "var(--atlas-text-secondary)",
            fontFamily: "monospace", fontSize: 10,
            borderRadius: 2, cursor: "pointer",
            textTransform: "uppercase"
          }}
        >
          Manter atual
        </button>
      </div>
    </div>
  );
}