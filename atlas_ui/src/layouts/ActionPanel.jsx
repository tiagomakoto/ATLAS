// atlas_ui/src/components/ActionPanel.jsx
import React, { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";

export default function ActionPanel({ activeTicker, onTickerChange }) {
  const [ativos, setAtivos] = useState([]);
  const [config, setConfig] = useState(null);
  const [editing, setEditing] = useState(false);
  const [editedConfig, setEditedConfig] = useState("");

  useEffect(() => {
    async function fetchAtivos() {
      try {
        const res = await fetch(`${API_BASE}/ativos`);
        const data = await res.json();
        setAtivos(data.ativos || []);
      } catch (err) {
        console.error("Erro ao buscar ativos:", err);
      }
    }
    fetchAtivos();
  }, []);

  useEffect(() => {
    if (!activeTicker) return;

    async function fetchConfig() {
      try {
        const res = await fetch(`${API_BASE}/ativos/${activeTicker}`);
        const data = await res.json();
        setConfig(data.config || data);
        setEditedConfig(JSON.stringify(data.config || data, null, 2));
      } catch (err) {
        console.error("Erro ao buscar config:", err);
      }
    }
    fetchConfig();
  }, [activeTicker]);

  const handleSave = async () => {
    try {
      const parsed = JSON.parse(editedConfig);
      const res = await fetch(`${API_BASE}/ativos/${activeTicker}/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          data: parsed,
          description: "Atualização via ActionPanel",
          confirm: true
        })
      });
      if (res.ok) {
        setEditing(false);
        setConfig(parsed);
      }
    } catch (err) {
      console.error("Erro ao salvar:", err);
    }
  };

  return (
    <aside style={{ 
      width: 300, 
      borderLeft: "1px solid var(--atlas-border)", 
      padding: 20, 
      background: "var(--atlas-surface)",
      overflowY: "auto"
    }}>
      {/* Seletor de Ativo */}
      <div style={{ marginBottom: 20 }}>
        <label style={{ 
          display: "block",
          fontFamily: "monospace", 
          fontSize: 9,
          color: "var(--atlas-text-secondary)",
          textTransform: "uppercase",
          marginBottom: 6
        }}>
          Ativo
        </label>
        <select
          value={activeTicker || ""}
          onChange={(e) => onTickerChange(e.target.value)}
          style={{
            width: "100%",
            padding: "8px 12px",
            background: "var(--atlas-bg)",
            border: "1px solid var(--atlas-border)",
            color: "var(--atlas-text-primary)",
            fontFamily: "monospace",
            fontSize: 11,
            borderRadius: 2
          }}
        >
          <option value="">Selecione...</option>
          {ativos.map((ticker) => (
            <option key={ticker} value={ticker}>
              {ticker}
            </option>
          ))}
        </select>
      </div>

      {/* ConfigEditor — ✅ C03: Tipografia como LABEL */}
      {activeTicker && (
        <div style={{ marginBottom: 20 }}>
          {/* ✅ C03: Label discreto, secundário */}
          <label style={{ 
            display: "block",
            fontFamily: "monospace", 
            fontSize: 9,
            color: "var(--atlas-text-secondary)",
            textTransform: "uppercase",
            marginBottom: 6,
            letterSpacing: 0.5
          }}>
            Configuração
          </label>

          {/* ✅ C03: Editor com estilo de label (não campo proeminente) */}
          <div style={{
            background: "var(--atlas-bg)",
            border: "1px solid var(--atlas-border)",
            borderRadius: 2,
            padding: 8,
            fontFamily: "monospace",
            fontSize: 9,  // ✅ C03: Menor (era 11-12)
            color: "var(--atlas-text-secondary)",  // ✅ C03: Cor secundária
            lineHeight: 1.4,
            whiteSpace: "pre-wrap",
            wordBreak: "break-all",
            maxHeight: 200,
            overflowY: "auto"
          }}>
            {editing ? (
              <textarea
                value={editedConfig}
                onChange={(e) => setEditedConfig(e.target.value)}
                style={{
                  width: "100%",
                  minHeight: 150,
                  background: "transparent",
                  border: "none",
                  color: "var(--atlas-text-secondary)",
                  fontFamily: "monospace",
                  fontSize: 9,
                  resize: "vertical"
                }}
              />
            ) : (
              <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
                {JSON.stringify(config, null, 2)}
              </pre>
            )}
          </div>

          {/* Ações */}
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            {editing ? (
              <>
                <button
                  onClick={handleSave}
                  style={{
                    flex: 1,
                    padding: "6px 12px",
                    background: "var(--atlas-blue)",
                    border: "none",
                    color: "#fff",
                    fontFamily: "monospace",
                    fontSize: 9,
                    borderRadius: 2,
                    cursor: "pointer",
                    textTransform: "uppercase"
                  }}
                >
                  Salvar
                </button>
                <button
                  onClick={() => setEditing(false)}
                  style={{
                    flex: 1,
                    padding: "6px 12px",
                    background: "var(--atlas-surface)",
                    border: "1px solid var(--atlas-border)",
                    color: "var(--atlas-text-secondary)",
                    fontFamily: "monospace",
                    fontSize: 9,
                    borderRadius: 2,
                    cursor: "pointer",
                    textTransform: "uppercase"
                  }}
                >
                  Cancelar
                </button>
              </>
            ) : (
              <button
                onClick={() => setEditing(true)}
                style={{
                  width: "100%",
                  padding: "6px 12px",
                  background: "var(--atlas-surface)",
                  border: "1px solid var(--atlas-border)",
                  color: "var(--atlas-text-secondary)",
                  fontFamily: "monospace",
                  fontSize: 9,
                  borderRadius: 2,
                  cursor: "pointer",
                  textTransform: "uppercase"
                }}
              >
                Editar
              </button>
            )}
          </div>
        </div>
      )}

      {/* Status do Ciclo */}
      <div style={{ marginBottom: 20 }}>
        <label style={{ 
          display: "block",
          fontFamily: "monospace", 
          fontSize: 9,
          color: "var(--atlas-text-secondary)",
          textTransform: "uppercase",
          marginBottom: 6
        }}>
          Ciclo Atual
        </label>
        <div style={{ 
          padding: 8, 
          background: "var(--atlas-bg)", 
          border: "1px solid var(--atlas-border)",
          borderRadius: 2,
          fontFamily: "monospace",
          fontSize: 10,
          color: "var(--atlas-text-primary)"
        }}>
          {activeTicker ? (
            <>
              <div><strong>Ativo:</strong> {activeTicker}</div>
              <div><strong>Status:</strong> Ativo</div>
            </>
          ) : (
            <span style={{ color: "var(--atlas-text-secondary)" }}>
              Selecione um ativo
            </span>
          )}
        </div>
      </div>

      {/* Ações Rápidas */}
      <div>
        <label style={{ 
          display: "block",
          fontFamily: "monospace", 
          fontSize: 9,
          color: "var(--atlas-text-secondary)",
          textTransform: "uppercase",
          marginBottom: 6
        }}>
          Ações
        </label>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <button
            style={{
              padding: "8px 12px",
              background: "var(--atlas-blue)",
              border: "none",
              color: "#fff",
              fontFamily: "monospace",
              fontSize: 10,
              borderRadius: 2,
              cursor: "pointer",
              textTransform: "uppercase"
            }}
          >
            Forçar Leitura
          </button>
          <button
            style={{
              padding: "8px 12px",
              background: "var(--atlas-surface)",
              border: "1px solid var(--atlas-border)",
              color: "var(--atlas-text-secondary)",
              fontFamily: "monospace",
              fontSize: 10,
              borderRadius: 2,
              cursor: "pointer",
              textTransform: "uppercase"
            }}
          >
            Exportar Config
          </button>
        </div>
      </div>
    </aside>
  );
}