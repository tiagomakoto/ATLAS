// atlas_ui/src/layouts/ActionPanel.jsx
import React, { useState, useEffect } from "react";
import ConfirmDialog from "../components/ConfirmDialog";

const API_BASE = "http://localhost:8000";

export default function ActionPanel({ activeTicker, onTickerChange }) {
  const [ativos, setAtivos] = useState([]);
  const [config, setConfig] = useState(null);
  const [tp, setTp] = useState("");
  const [stop, setStop] = useState("");
  const [saving, setSaving] = useState(false);
  const [diff, setDiff] = useState(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [description, setDescription] = useState("");
  const [saveError, setSaveError] = useState(null);

  // Carregar lista de ativos
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

  // Carregar config ao selecionar ativo
  useEffect(() => {
    if (!activeTicker) return;
    async function fetchConfig() {
      try {
        const res = await fetch(`${API_BASE}/ativos/${activeTicker}`);
        const data = await res.json();
        setConfig(data);
        setTp(String(data.take_profit ?? ""));
        setStop(String(data.stop_loss ?? ""));
        setDiff(null);
      } catch (err) {
        console.error("Erro ao buscar config:", err);
      }
    }
    fetchConfig();
  }, [activeTicker]);

  // Ver diff antes de salvar
  async function handleVerDiff() {
    try {
      const res = await fetch(`${API_BASE}/config/diff`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          data: {
            take_profit: parseFloat(tp),
            stop_loss: parseFloat(stop)
          }
        })
      });
      const result = await res.json();
      setDiff(result);
      setConfirmOpen(true);
    } catch (err) {
      console.error("Erro ao calcular diff:", err);
      setSaveError("Erro ao calcular diff");
      setTimeout(() => setSaveError(null), 5000);
    }
  }

  // Salvar após confirmação
  async function handleSave() {
    if (!description.trim()) return;
    setSaving(true);
    try {
      await fetch(`${API_BASE}/ativos/${activeTicker}/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          data: {
            take_profit: parseFloat(tp),
            stop_loss: parseFloat(stop)
          },
          description: description.trim(),
          confirm: true
        })
      });
      setDiff(null);
      setDescription("");
      setConfirmOpen(false);
      setConfig(prev => prev ? { ...prev, take_profit: parseFloat(tp), stop_loss: parseFloat(stop) } : null);
    } catch (err) {
      console.error("Erro ao salvar:", err);
      setSaveError("Erro ao salvar configuração");
      setTimeout(() => setSaveError(null), 5000);
    } finally {
      setSaving(false);
    }
  }

  // Estilos
  const labelStyle = {
    fontFamily: "monospace",
    fontSize: 9,
    color: "var(--atlas-text-secondary)",
    textTransform: "uppercase",
    display: "block",
    marginBottom: 4
  };

  const inputStyle = {
    width: "100%",
    padding: "6px 8px",
    background: "var(--atlas-bg)",
    border: "1px solid var(--atlas-border)",
    color: "var(--atlas-text-primary)",
    fontFamily: "monospace",
    fontSize: 11,
    borderRadius: 2
  };

  const hintStyle = {
    fontFamily: "monospace",
    fontSize: 9,
    color: "var(--atlas-text-secondary)",
    marginTop: 2
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
        <label style={labelStyle}>Ativo</label>
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

      {/* Config Editor — APENAS TP E STOP (A04) */}
      {activeTicker && (
        <div style={{ marginBottom: 20 }}>
          <label style={labelStyle}>Configuração</label>
          
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {/* Take Profit */}
            <div>
              <label style={labelStyle}>Take Profit</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                max="0.99"
                value={tp}
                onChange={(e) => { setTp(e.target.value); setDiff(null); }}
                style={inputStyle}
                disabled={!config}
              />
              <div style={hintStyle}>Proporção do prêmio (ex: 0.90 = 90%)</div>
            </div>

            {/* Stop Loss */}
            <div>
              <label style={labelStyle}>Stop Loss</label>
              <input
                type="number"
                step="0.1"
                min="0.1"
                value={stop}
                onChange={(e) => { setStop(e.target.value); setDiff(null); }}
                style={inputStyle}
                disabled={!config}
              />
              <div style={hintStyle}>Múltiplo do prêmio (ex: 2.0 = 2×)</div>
            </div>

            {/* Botões */}
            <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
              <button
                onClick={handleVerDiff}
                disabled={!tp || !stop || saving}
                style={{
                  flex: 1,
                  padding: "6px 12px",
                  background: "var(--atlas-blue)",
                  border: "none",
                  color: "#fff",
                  fontFamily: "monospace",
                  fontSize: 9,
                  borderRadius: 2,
                  cursor: (!tp || !stop || saving) ? "not-allowed" : "pointer",
                  textTransform: "uppercase",
                  opacity: (!tp || !stop || saving) ? 0.6 : 1
                }}
              >
                {saving ? "Carregando..." : "Ver Diff"}
              </button>
            </div>
          </div>

          {/* ConfirmDialog */}
          <ConfirmDialog
            open={confirmOpen}
            diff={diff}
            description={description}
            onDescriptionChange={setDescription}
            onConfirm={handleSave}
            onCancel={() => { setConfirmOpen(false); setDiff(null); }}
          />

          {/* Feedback de erro */}
          {saveError && (
            <div style={{
              marginTop: 8,
              padding: "4px 8px",
              background: "rgba(239, 68, 68, 0.9)",
              color: "#fff",
              fontSize: 9,
              fontFamily: "monospace",
              borderRadius: 2
            }}>
              {saveError}
            </div>
          )}
        </div>
      )}

      {/* Status do Ciclo */}
      <div style={{ marginBottom: 20 }}>
        <label style={labelStyle}>Ciclo Atual</label>
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
              <div><strong>Ativo: </strong> {activeTicker}</div>
              <div><strong>Status: </strong> {config?.status || "—"}</div>
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
        <label style={labelStyle}>Ações</label>
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