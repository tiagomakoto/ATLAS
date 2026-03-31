// atlas_ui/src/layouts/Manutencao.jsx
import React from "react";
import Configuracao from "../components/Configuracao";
import EOD from "../components/EOD";
import Versionamento from "../components/Versionamento";

export default function Manutencao({ activeTicker }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      
      {/* ✅ Configuração — 50% width */}
      <div style={{ maxWidth: "50%" }}>
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
            marginBottom: 16
          }}>
            Configuração
          </div>
          <Configuracao ticker={activeTicker} />
        </div>
      </div>

      {/* ✅ EOD — 50% width */}
      <div style={{ maxWidth: "50%" }}>
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
            marginBottom: 16
          }}>
            Upload EOD
          </div>
          <EOD />
        </div>
      </div>

      {/* ✅ Versionamento — 50% width */}
      <div style={{ maxWidth: "50%" }}>
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
            marginBottom: 16
          }}>
            Versionamento
          </div>
          <Versionamento ticker={activeTicker} />
        </div>
      </div>
    </div>
  );
}