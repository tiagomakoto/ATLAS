// atlas_ui/src/components/Header.jsx
import React from "react";
import Tooltip from "./Tooltip";
import ModeToggle from "./ModeToggle";

export default function Header({ state, cycleData, mode }) {
  const health = state?.health || "unknown";
  const healthReason = state?.health_reason || "";
  
  const ativo = cycleData?.ativo || "—";
  const regime = cycleData?.regime || "DESCONHECIDO";
  const posicao = cycleData?.posicao || "OFF";
  const ir = cycleData?.pnl || 0;
  const confianca = cycleData?.regime_confianca || 0;

  const getRegimeColor = (regime) => {
    if (!regime) return "var(--atlas-text-secondary)";
    const r = regime.toUpperCase();
    if (r.includes("ALTA") || r.includes("BULL")) return "var(--atlas-green)";
    if (r.includes("BAIXA") || r.includes("BEAR")) return "var(--atlas-red)";
    if (r.includes("TRANSICAO") || r.includes("TRANSIÇÃO")) return "var(--atlas-amber)";
    if (r.includes("NEUTRO")) return "var(--atlas-blue)";
    return "var(--atlas-text-primary)";
  };

  return (
    <header
      className={`global-header ${mode === "execution" ? "executing" : ""}`}
      style={{
        borderBottom: "1px solid var(--atlas-border)",
        background: "var(--atlas-surface)",
        padding: "12px 20px"
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        
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
              background: health === "ok" ? "var(--atlas-green)" : "var(--atlas-amber)",
              boxShadow: `0 0 8px ${health === "ok" ? "var(--atlas-green)" : "var(--atlas-amber)"}`
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

        <div style={{ width: 2, height: 24, background: "var(--atlas-border)", margin: "0 8px" }} />

        {/* Cards de Métricas */}
        <div style={{ 
          display: "flex", 
          gap: 8, 
          padding: "8px 12px", 
          background: "var(--atlas-bg)", 
          border: "1px solid var(--atlas-border)", 
          borderRadius: 4 
        }}>
          
          {/* Ativo */}
          <Tooltip 
            content={
              <div style={{ lineHeight: 1.6 }}>
                <div><strong>ATIVO</strong></div>
                <div style={{ marginTop: 4 }}>{ativo}</div>
              </div>
            } 
            position="bottom" 
            delay={600}
          >
            <div style={{ padding: "4px 8px", borderRight: "1px solid var(--atlas-border)" }}>
              <span style={{ 
                fontFamily: "monospace", 
                fontSize: 11, 
                fontWeight: "bold", 
                color: "var(--atlas-green)" 
              }}>
                {ativo}
              </span>
            </div>
          </Tooltip>

          {/* Regime */}
          <Tooltip 
            content={
              <div style={{ lineHeight: 1.6 }}>
                <div><strong>REGIME</strong></div>
                <div style={{ marginTop: 4 }}>Classificação ORBIT</div>
              </div>
            } 
            position="bottom" 
            delay={600}
          >
            <div style={{ padding: "4px 8px", borderRight: "1px solid var(--atlas-border)" }}>
              <div style={{ fontSize: 8, color: "var(--atlas-text-secondary)", marginBottom: 2 }}>
                REGIME:
              </div>
              <span style={{ 
                fontFamily: "monospace", 
                fontSize: 10, 
                fontWeight: "bold", 
                color: getRegimeColor(regime) 
              }}>
                {regime.replace("_", " ")}
              </span>
            </div>
          </Tooltip>

          {/* Posição */}
          <Tooltip 
            content={
              <div style={{ lineHeight: 1.6 }}>
                <div><strong>POSIÇÃO</strong></div>
                <div style={{ marginTop: 4 }}>• ON: Exposto • OFF: Protegido</div>
              </div>
            } 
            position="bottom" 
            delay={600}
          >
            <div style={{ padding: "4px 8px", borderRight: "1px solid var(--atlas-border)" }}>
              <div style={{ fontSize: 8, color: "var(--atlas-text-secondary)", marginBottom: 2 }}>
                POSIÇÃO:
              </div>
              <span style={{ 
                fontFamily: "monospace", 
                fontSize: 10, 
                fontWeight: "bold", 
                color: posicao === "ON" ? "var(--atlas-green)" : "var(--atlas-amber)" 
              }}>
                {posicao}
              </span>
            </div>
          </Tooltip>

          {/* IR */}
          <Tooltip 
            content={
              <div style={{ lineHeight: 1.6 }}>
                <div><strong>IR</strong></div>
                <div style={{ marginTop: 4 }}>Performance do ciclo</div>
                <div style={{ marginTop: 4, color: "var(--atlas-amber)", fontSize: 9 }}>
                  ⚠ Não inclui seguro
                </div>
              </div>
            } 
            position="bottom" 
            delay={600}
          >
            <div style={{ padding: "4px 8px", borderRight: "1px solid var(--atlas-border)" }}>
              <div style={{ fontSize: 8, color: "var(--atlas-text-secondary)", marginBottom: 2 }}>
                IR:
              </div>
              <span style={{ 
                fontFamily: "monospace", 
                fontSize: 10, 
                fontWeight: "bold", 
                color: ir >= 0 ? "var(--atlas-green)" : "var(--atlas-red)" 
              }}>
                {typeof ir === "number" ? ir.toFixed(3) : "—"}
              </span>
            </div>
          </Tooltip>

          {/* Confiança */}
          <Tooltip 
            content={
              <div style={{ lineHeight: 1.6 }}>
                <div><strong>CONFIANÇA</strong></div>
                <div style={{ marginTop: 4 }}>Score ORBIT (0-100%)</div>
              </div>
            } 
            position="bottom" 
            delay={600}
          >
            <div style={{ padding: "4px 8px" }}>
              <div style={{ fontSize: 8, color: "var(--atlas-text-secondary)", marginBottom: 2 }}>
                CONFIANÇA:
              </div>
              <span style={{ 
                fontFamily: "monospace", 
                fontSize: 10, 
                fontWeight: "bold", 
                color: confianca > 0.7 ? "var(--atlas-green)" : confianca > 0.4 ? "var(--atlas-amber)" : "var(--atlas-red)" 
              }}>
                {(confianca * 100).toFixed(1)}%
              </span>
            </div>
          </Tooltip>
        </div>

        <div style={{ flex: 1 }} />

        {/* ModeToggle */}
        <ModeToggle mode={mode} />
      </div>
    </header>
  );
}