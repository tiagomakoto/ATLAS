import { useState } from "react";

export default function StatusTransitionCard({ ticker, status_anterior, status_novo, ciclo }) {
  const [confirmado, setConfirmado] = useState(false);

  if (confirmado) return null;

  const handleConfirmar = () => {
    setConfirmado(true);
  };

  const handleRevisar = () => {
    // Navega para aba Ativo → ORBIT do ticker
    window.dispatchEvent(new CustomEvent("atlas:navigate", {
      detail: { tab: "ativo", ticker, internalTab: "orbit" }
    }));
  };

  return (
    <div style={{
      padding: 14,
      background: "rgba(16,185,129,0.08)",
      border: "1px solid var(--atlas-green)",
      borderRadius: 2,
      fontFamily: "monospace", fontSize: 11
    }}>
      <div style={{
        color: "var(--atlas-green)", fontSize: 9,
        textTransform: "uppercase", letterSpacing: 1,
        marginBottom: 10
      }}>
        ↑ {ticker} — status atualizado ({ciclo})
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
            Anterior
          </div>
          <div style={{ color: "var(--atlas-amber)" }}>
            <strong>{status_anterior}</strong>
          </div>
        </div>
        <div style={{
          padding: 8,
          background: "rgba(16,185,129,0.1)",
          borderRadius: 2
        }}>
          <div style={{ fontSize: 9,
                        color: "var(--atlas-green)",
                        marginBottom: 4 }}>
            Novo
          </div>
          <div style={{ color: "var(--atlas-green)" }}>
            <strong>{status_novo}</strong>
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <button
          onClick={handleConfirmar}
          style={{
            padding: "6px 16px",
            background: "var(--atlas-green)",
            border: "none", color: "#fff",
            fontFamily: "monospace", fontSize: 10,
            borderRadius: 2, cursor: "pointer",
            textTransform: "uppercase"
          }}
        >
          Confirmar
        </button>
        <button
          onClick={handleRevisar}
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
          Revisar antes
        </button>
      </div>
    </div>
  );
}
