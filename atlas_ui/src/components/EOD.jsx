// atlas_ui/src/components/EOD.jsx
import React, { useState } from "react";

export default function EOD() {
  const [uploading, setUploading] = useState(false);

  async function handleUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    console.log("Upload EOD:", file.name);
    setUploading(false);
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
        Upload de Arquivos EOD
      </div>

      <div style={{
        padding: 40,
        border: "2px dashed var(--atlas-border)",
        borderRadius: 4,
        textAlign: "center"
      }}>
        <div style={{
          fontFamily: "monospace",
          fontSize: 11,
          color: "var(--atlas-text-secondary)",
          marginBottom: 12
        }}>
          Formatos aceitos: .csv, .parquet
        </div>

        <input
          type="file"
          accept=".csv,.parquet"
          onChange={handleUpload}
          disabled={uploading}
          style={{
            fontFamily: "monospace",
            fontSize: 10,
            color: "var(--atlas-text-primary)"
          }}
        />

        {uploading && (
          <div style={{
            marginTop: 12,
            fontFamily: "monospace",
            fontSize: 10,
            color: "var(--atlas-amber)"
          }}>
            Processando...
          </div>
        )}
      </div>

      <div style={{
        marginTop: 16,
        padding: "8px 12px",
        background: "var(--atlas-surface)",
        border: "1px solid var(--atlas-border)",
        borderRadius: 4,
        fontFamily: "monospace",
        fontSize: 9,
        color: "var(--atlas-text-secondary)"
      }}>
        <div style={{ marginBottom: 4 }}><strong>Tipos de arquivo:</strong></div>
        <div>• Dados EOD de opções (greeks, OI, volume)</div>
        <div>• Calendário de eventos (earnings, dividendos, macro)</div>
      </div>
    </div>
  );
}