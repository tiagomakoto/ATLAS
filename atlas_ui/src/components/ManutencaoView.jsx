// atlas_ui/src/components/ManutencaoView.jsx

import React, { useState } from "react";

const API_BASE = "http://localhost:8000";

export default function ManutencaoView() {
  const [novoAtivo, setNovoAtivo] = useState("");
  const [onboarding, setOnboarding] = useState(false);
  const [onboardingMsg, setOnboardingMsg] = useState("");

  async function handleOnboarding() {
    if (!novoAtivo.trim()) return;
    setOnboarding(true);
    setOnboardingMsg("");
    try {
      const res = await fetch(`${API_BASE}/delta-chaos/onboarding`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: novoAtivo.trim().toUpperCase(),
          confirm: true,
          description: `Onboarding ${novoAtivo.trim().toUpperCase()}`
        })
      });
      const data = await res.json();
      setOnboardingMsg(
        res.ok
          ? `✓ ${novoAtivo.toUpperCase()} — onboarding iniciado`
          : `✗ ${data.detail || "Erro desconhecido"}`
      );
    } catch (e) {
      setOnboardingMsg(`✗ Erro: ${e.message}`);
    } finally {
      setOnboarding(false);
      setNovoAtivo("");
    }
  }

  async function exportarConfig() {
    try {
        const res = await fetch(`${API_BASE}/report`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ state: {}, analytics: {}, staleness: 0 })
        });
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `atlas_config_${new Date().toISOString().slice(0,10)}.md`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        console.error("Erro ao exportar:", e);
    }
  }

  const labelStyle = {
    fontFamily: "monospace", fontSize: 9,
    color: "var(--atlas-text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.08em", marginBottom: 8, display: "block"
  };

  const sectionStyle = {
    padding: 14,
    background: "var(--atlas-surface)",
    border: "1px solid var(--atlas-border)",
    borderRadius: 2,
    marginBottom: 16
  };

  return (
    <div style={{
      display: "flex", flexDirection: "column", gap: 16,
      maxWidth: 480,
      padding: 20
    }}>

      {/* Onboarding novo ativo */}
      <div style={sectionStyle}>
        <span style={labelStyle}>Onboarding de novo ativo</span>
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <input
            value={novoAtivo}
            onChange={e => setNovoAtivo(e.target.value.toUpperCase())}
            placeholder="Ex: WEGE3"
            maxLength={6}
            style={{
              flex: 1, padding: "6px 10px",
              background: "var(--atlas-bg)",
              border: "1px solid var(--atlas-border)",
              color: "var(--atlas-text-primary)",
              fontFamily: "monospace", fontSize: 11,
              borderRadius: 2,
              textTransform: "uppercase"
            }}
          />
          <button
            onClick={handleOnboarding}
            disabled={!novoAtivo.trim() || onboarding}
            style={{
              padding: "6px 14px",
              background: (!novoAtivo.trim() || onboarding)
                ? "var(--atlas-border)"
                : "var(--atlas-blue)",
              border: "none", color: "#fff",
              fontFamily: "monospace", fontSize: 10,
              borderRadius: 2, cursor: "pointer",
              textTransform: "uppercase"
            }}
          >
            {onboarding ? "..." : "Iniciar"}
          </button>
        </div>
        {onboardingMsg && (
          <div style={{
            fontFamily: "monospace", fontSize: 10,
            color: onboardingMsg.startsWith("✓")
              ? "var(--atlas-green)"
              : "var(--atlas-red)"
          }}>
            {onboardingMsg}
          </div>
        )}
        <div style={{
          marginTop: 8, fontFamily: "monospace", fontSize: 9,
          color: "var(--atlas-text-secondary)"
        }}>
          Sequência automática: TAPE → ORBIT → TUNE → GATE
        </div>
      </div>

      {/* Exportar */}
      <div style={sectionStyle}>
        <span style={labelStyle}>Exportar</span>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={exportarConfig}
            style={{
              padding: "6px 14px",
              background: "var(--atlas-surface)",
              border: "1px solid var(--atlas-border)",
              color: "var(--atlas-text-secondary)",
              fontFamily: "monospace", fontSize: 10,
              borderRadius: 2, cursor: "pointer",
              textTransform: "uppercase"
            }}
          >
            Relatório de sessão
          </button>
        </div>
      </div>

    </div>
  );
}
