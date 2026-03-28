// atlas_ui/src/components/PosicoesTable.jsx
import React from "react";
import Tooltip from "./Tooltip";

export default function PosicoesTable({ posicoes, fonte }) {
  if (!posicoes?.length) {
    return (
      <div style={{ fontFamily: "monospace", fontSize: 11, color: "var(--atlas-text-secondary)", padding: 8 }}>
        Nenhuma posição aberta ({fonte?.toUpperCase()})
      </div>
    );
  }

  const fonteLabel = fonte === "paper" ? "🟡 PAPER" : fonte === "live" ? "🔴 LIVE" : "🔵 BACKTEST";

  return (
    <>
      <div style={{
        fontFamily: "monospace",
        fontSize: 10,
        color: "var(--atlas-text-secondary)",
        marginBottom: 4,
        paddingBottom: 4,
        borderBottom: "1px solid var(--atlas-border)"
      }}>
        {fonteLabel}
      </div>
      <table style={{ width: "100%", fontFamily: "monospace", fontSize: 11, borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ borderBottom: "1px solid var(--atlas-border)", textAlign: "left" }}>
            <th style={{ padding: 8 }}>Ativo</th>
            <th style={{ padding: 8 }}>Estratégia</th>
            <th style={{ padding: 8 }}>Tipo vol</th>
            <th style={{ padding: 8 }}>Horizonte</th>
            <th style={{ padding: 8 }}>Entrada</th>
            <th style={{ padding: 8 }}>DTE</th>
            <th style={{ padding: 8 }}>Regime entrada</th>
            <th style={{ padding: 8 }}>IR esperado (IC95%)</th>
            <th style={{ padding: 8 }}>TP</th>
            <th style={{ padding: 8 }}>Stop</th>
            <th style={{ padding: 8 }}>
              <Tooltip
                content={
                  <div style={{ lineHeight: 1.6 }}>
                    <div><strong>P&L ATUAL</strong></div>
                    <div style={{ marginTop: 4 }}>Resultado da posição em tempo real</div>
                    <div style={{ marginTop: 4, color: "var(--atlas-amber)", fontSize: 9 }}>
                      ⚠ Não inclui P&L do seguro estrutural (PUT ITM)
                    </div>
                  </div>
                }
                position="bottom"
                delay={600}
              >
                <span style={{ textDecoration: "underline dotted var(--atlas-text-secondary)" }}>
                  P&L atual
                </span>
              </Tooltip>
            </th>
            {/* ✅ C01: Nova coluna P&L Estrutural */}
            <th style={{ padding: 8 }}>
              <Tooltip
                content={
                  <div style={{ lineHeight: 1.6 }}>
                    <div><strong>P&L ESTRUTURAL</strong></div>
                    <div style={{ marginTop: 4 }}>Hedge de cauda (PUT ITM long vol)</div>
                    <div style={{ marginTop: 4, color: "var(--atlas-text-secondary)", fontSize: 9 }}>
                      Consolidado separadamente do operacional
                    </div>
                  </div>
                }
                position="bottom"
                delay={600}
              >
                <span style={{ textDecoration: "underline dotted var(--atlas-text-secondary)" }}>
                  P&L Estrutural
                </span>
              </Tooltip>
            </th>
          </tr>
        </thead>
        <tbody>
          {posicoes.map((pos, idx) => {
            const core = pos.core || {};
            const orbit = pos.orbit || {};
            const legs = pos.legs || [];
            const dte = legs[0]?.vencimento
              ? Math.floor((new Date(legs[0].vencimento) - new Date()) / (1000 * 60 * 60 * 24))
              : 0;
            
            // ✅ C01: P&L estrutural neutro (separado do operacional)
            const pnlEstrutural = 0; // Será preenchido quando o book_manager retornar

            return (
              <tr key={pos.op_id || idx} style={{ borderBottom: "1px solid var(--atlas-border)" }}>
                <td style={{ padding: 8, fontWeight: "bold" }}>{core.ativo || "—"}</td>
                <td style={{ padding: 8 }}>{core.estrategia || "—"}</td>
                <td style={{ padding: 8 }}>{legs[0]?.tipo || "—"}</td>
                <td style={{ padding: 8 }}>{dte}d</td>
                <td style={{ padding: 8 }}>{core.data_entrada || "—"}</td>
                <td style={{ padding: 8, color: dte < 7 ? "var(--atlas-red)" : "inherit"}}>{dte}</td>
                <td style={{ padding: 8 }}>{orbit.regime_entrada || "—"}</td>
                <td style={{ padding: 8 }}>{orbit.ir_orbit ? orbit.ir_orbit.toFixed(2) : "—"}</td>
                <td style={{ padding: 8 }}>TP</td>
                <td style={{ padding: 8 }}>Stop</td>
                <td style={{ padding: 8, color: (core.pnl || 0) >= 0 ? "var(--atlas-green)" : "var(--atlas-red)" }}>
                  {core.pnl ? core.pnl.toFixed(2) : "—"}
                </td>
                {/* ✅ C01: P&L Estrutural (neutro, separado) */}
                <td style={{ padding: 8, color: "var(--atlas-text-secondary)", fontStyle: "italic" }}>
                  {pnlEstrutural !== 0 ? pnlEstrutural.toFixed(2) : "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </>
  );
}