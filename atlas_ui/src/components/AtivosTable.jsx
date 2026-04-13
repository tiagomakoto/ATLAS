// atlas_ui/src/components/AtivosTable.jsx
import React from "react";
import Tooltip from "./Tooltip";
import { useSystemStore } from "../store/systemStore";

const statusColors = {
  OPERAR: "var(--atlas-green)",
  MONITORAR: "var(--atlas-amber)",
  SUSPENSO: "var(--atlas-red)",
  SEM_EDGE: "var(--atlas-text-secondary)",
};

// ✅ Função para cor do regime
const getRegimeColor = (regime) => {
  if (!regime) return "var(--atlas-text-secondary)";
  const r = regime.toUpperCase();
  
  // 🟢 Regimes de alta / bull
  if (r.includes("ALTA") || r.includes("BULL")) return "var(--atlas-green)";
  
  // 🔴 Regimes de baixa / bear / pânico
  if (r.includes("BAIXA") || r.includes("BEAR") || r.includes("PANICO")) return "var(--atlas-red)";
  
  // 🟡 Regimes de transição / recuperação
  if (r.includes("TRANSICAO") || r.includes("TRANSIÇÃO") || r.includes("RECUPERACAO")) return "var(--atlas-amber)";
  
  // 🔵 Regimes neutros / laterais
  if (r.includes("NEUTRO") || r.includes("LATERAL") || r.includes("MORTO")) return "var(--atlas-blue)";
  
  // ⚪ Fallback
  return "var(--atlas-text-secondary)";
};

export default function AtivosTable() {
  const ativosParametrizados = useSystemStore(s => s.ativosParametrizados);
  const ativos = ativosParametrizados || [];
  
  if (!ativos || ativos.length === 0) {
    return (
      <div style={{ fontFamily: "monospace", fontSize: 11, color: "var(--atlas-text-secondary)", padding: 8 }}>
        Nenhum ativo parametrizado
      </div>
    );
  }

  return (
    <table style={{ width: "100%", fontFamily: "monospace", fontSize: 11, borderCollapse: "collapse" }}>
      <thead>
        <tr style={{ borderBottom: "1px solid var(--atlas-border)", textAlign: "left" }}>
          <th style={{ padding: 8 }}>Ativo</th>
          <th style={{ padding: 8 }}>Status</th>
          <th style={{ padding: 8 }}>Último ciclo</th>
          
          {/* Coluna IR com tooltip */}
          <th style={{ padding: 8 }}>
            <Tooltip
              content={
                <div style={{ lineHeight: 1.6 }}>
                  <div><strong>INFORMATION RATIO (IR)</strong></div>
                  <div style={{ marginTop: 4 }}>
                    Retorno ajustado ao risco do último ciclo.
                  </div>
                  <div style={{ marginTop: 4, fontSize: 9 }}>
                    • IR &gt; 0: Retorno positivo ajustado à volatilidade
                  </div>
                  <div>• IR &lt; 0: Retorno negativo ajustado à volatilidade</div>
                  <div>• |IR| &gt; 1.0: Edge estatisticamente significativo</div>
                </div>
              }
              position="bottom"
              delay={600}
            >
              <span style={{ textDecoration: "underline dotted var(--atlas-text-secondary)" }}>
                IR
              </span>
            </Tooltip>
          </th>
          
          {/* Estratégia com tooltip */}
          <th style={{ padding: 8 }}>
            <Tooltip
              content={
                <div style={{ lineHeight: 1.6 }}>
                  <div><strong>ESTRATÉGIA</strong></div>
                  <div style={{ marginTop: 4 }}>Tipo de operação configurada</div>
                  <div style={{ marginTop: 4, fontSize: 9 }}>
                    • Short Vol: Venda de opções OTM
                  </div>
                  <div>• Long Vol: Compra de opções ITM</div>
                  <div>• Delta Neutral: Hedge de direção</div>
                  <div>• Indefinida: Sem estratégia configurada</div>
                </div>
              }
              position="bottom"
              delay={600}
            >
              <span style={{ textDecoration: "underline dotted var(--atlas-text-secondary)" }}>
                Estratégia
              </span>
            </Tooltip>
          </th>
          
          <th style={{ padding: 8 }}>Regime</th>
          <th style={{ padding: 8 }}>Confiança</th>
            <th style={{ padding: 8 }}>REFLECT</th>
            <th style={{ padding: 8 }}>TP</th>
            <th style={{ padding: 8 }}>STOP</th>
          </tr>
        </thead>
      <tbody>
        {ativos.map((ativo) => {
          const ticker = ativo.ticker || "DESCONHECIDO";
          const status = ativo.status || "desconhecido";
          
          const historicoArray = Array.isArray(ativo.historico) ? ativo.historico : [];
          const lastCycle = historicoArray.slice(-1)[0] || ativo.core || {};
          
          const cicloId = lastCycle.ciclo_id || `${ativo.historico?.length || 0} ciclos`;
          
          // ✅ EXTRAIR IR DO ÚLTIMO CICLO
          const ir = lastCycle.ir ?? 0;
          const irColor = ir > 0 ? "var(--atlas-green)" : ir < 0 ? "var(--atlas-red)" : "var(--atlas-text-secondary)";
          
          // Estratégia do regime atual (de estrategias[regime])
          const regime = lastCycle.regime || "—";
          const estrategias = ativo.core?.estrategias || {};
          const estrategia = estrategias[regime] || "Indefinida";
          const regimeColor = getRegimeColor(regime);
          const score = lastCycle.score ?? lastCycle.regime_confianca ?? 0;
          
          const reflectState = ativo.reflect_state || "?";
          const reflectColor = reflectState === "A" ? "var(--atlas-green)" :
                               reflectState === "B" ? "var(--atlas-blue)" :
                               reflectState === "C" ? "var(--atlas-amber)" :
                               reflectState === "D" ? "var(--atlas-red)" :
                               "var(--atlas-text-secondary)";
          
          const statusColor = statusColors[status] || "var(--atlas-text-secondary)";
          
          // Cores por estratégia
          const estrategiaColor = 
            estrategia === "Indefinida" ? "var(--atlas-text-secondary)" :
            estrategia.includes("Short") ? "var(--atlas-red)" :
            estrategia.includes("Long") ? "var(--atlas-green)" :
            "var(--atlas-blue)";

          return (
            <tr
              key={ticker}
              style={{
                borderBottom: "1px solid var(--atlas-border)",
                opacity: status === "SEM_EDGE" ? 0.6 : 1,
              }}
            >
              <td style={{ padding: 8, fontWeight: "bold" }}>{ticker}</td>
              <td style={{ padding: 8, color: statusColor }}>● {status}</td>
              <td style={{ padding: 8 }}>{cicloId}</td>
              <td style={{ padding: 8, fontWeight: "bold", color: irColor }}>
                {ir.toFixed(3)}
              </td>
              
              {/* Estratégia com tooltip */}
              <td style={{ padding: 8 }}>
                <Tooltip
                  content={
                    <div style={{ lineHeight: 1.6 }}>
                      <div><strong>{estrategia}</strong></div>
                      <div style={{ marginTop: 4, fontSize: 9 }}>
                        {estrategia === "Indefinida" 
                          ? "Nenhuma estratégia configurada para este regime"
                          : estrategia.includes("Short") 
                          ? "Exposição: venda de volatilidade (theta positivo)"
                          : estrategia.includes("Long")
                          ? "Exposição: compra de volatilidade (vega positivo)"
                          : "Exposição: neutro a direção do mercado"}
                      </div>
                    </div>
                  }
                  position="bottom"
                  delay={600}
                >
                  <span style={{ 
                    color: estrategiaColor,
                    fontWeight: "bold",
                    textDecoration: "underline dotted var(--atlas-text-secondary)",
                    cursor: "help"
                  }}>
                    {estrategia}
                  </span>
                </Tooltip>
              </td>
              
              {/* ✅ REGIME COM COR */}
              <td style={{ padding: 8, color: regimeColor, fontWeight: "bold" }}>
                {regime}
              </td>
              
              <td style={{ padding: 8 }}>
                {score ? `${Math.abs(score * 100).toFixed(1)}%` : "—"}
              </td>
            <td style={{ padding: 8, textAlign: "center" }}>
              <span style={{ padding: "2px 8px", borderRadius: 2, fontSize: 9, background: reflectColor, color: "#fff", fontWeight: "bold" }}>
                {reflectState}
              </span>
            </td>
            <td style={{ padding: 8, textAlign: "right", fontFamily: "monospace" }}>
              {ativo.take_profit != null ? ativo.take_profit.toFixed(2) : <span style={{ color: "var(--atlas-text-secondary)" }}>—</span>}
            </td>
            <td style={{ padding: 8, textAlign: "right", fontFamily: "monospace" }}>
              {ativo.stop_loss != null ? ativo.stop_loss.toFixed(2) : <span style={{ color: "var(--atlas-text-secondary)" }}>—</span>}
            </td>
          </tr>
          );
        })}
      </tbody>
    </table>
  );
}