// atlas_ui/src/components/Header.jsx
import React from "react";
import Tooltip from "./Tooltip";
import ModeToggle from "./ModeToggle";

export default function Header({ state, cycleData, mode }) {
  const health = state?.health || "unknown";
  const healthReason = state?.health_reason || "";

  const getHealthColor = (health) => {
    if (health === "ok") return "var(--atlas-green)";
    if (health === "warning") return "var(--atlas-amber)";
    if (health === "error") return "var(--atlas-red)";
    return "var(--atlas-text-secondary)";
  };

  return (
    <header
      className={`global-header ${mode === "execution" ? "executing" : ""}`}
      style={{
        borderBottom: "1px solid var(--atlas-border)",
        background: "var(--atlas-surface)",
        padding: "12px 20px",
        width: "100%"
      }}
    >
      <div style={{ display: "flex", alignItems: "center", width: "100%" }}>
        
        {/* LADO ESQUERDO (0% - 62%) */}
        <div style={{ width: "62%", display: "flex", alignItems: "center", gap: 16 }}>
          
          {/* Saúde com Tooltip */}
          <Tooltip 
            content={
              <div style={{ lineHeight: 1.6 }}>
                <div><strong>STATUS DO SISTEMA</strong></div>
                <div style={{ marginTop: 4 }}>Status dos módulos ATLAS</div>
                {healthReason && (
                  <div style={{ marginTop: 4, color: "var(--atlas-amber)" }}>
                    {healthReason}
                  </div>
                )}
              </div>
            }
            position="bottom"
            delay={600}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "4px 8px" }}>
              <div style={{ 
                width: 8, 
                height: 8, 
                borderRadius: "50%",
                background: getHealthColor(health),
                boxShadow: `0 0 8px ${getHealthColor(health)}`
              }} />
              <span style={{ 
                fontFamily: "monospace", 
                fontSize: 9, 
                color: "var(--atlas-text-secondary)", 
                textTransform: "uppercase" 
              }}>
                Sistema operacional
              </span>
            </div>
          </Tooltip>

          {/* Título */}
          <span style={{ 
            fontFamily: "monospace", 
            fontSize: 16, 
            fontWeight: "bold", 
            letterSpacing: 3, 
            color: "var(--atlas-text-primary)" 
          }}>
            ATLAS
          </span>
        </div>

        {/* LADO DIREITO (62% - 100%) */}
        <div style={{ flex: 1, display: "flex", alignItems: "center" }}>
          {/* ModeToggle */}
          <ModeToggle mode={mode} />
        </div>

      </div>
    </header>
  );
}