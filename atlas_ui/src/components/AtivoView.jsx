import React, { useState, useEffect } from "react";
import WalkForwardChart from "../components/WalkForwardChart";
import DistributionChart from "../components/DistributionChart";
import ACFChart from "../components/ACFChart";
import TailMetrics from "../components/TailMetrics";
import Tooltip from "../components/Tooltip";
import { getRegimeColor, getRegimeBgColor } from "../store/regimeColors";
import RelatorioTab from "./RelatorioTab";

const API_BASE = "http://localhost:8000";

// === SUB-ABA: ORBIT ===
const OrbitTab = ({ ticker, data }) => {
  if (!data) {
    return (
      <div style={{ padding: 20, color: "var(--atlas-text-secondary)", textAlign: "center" }}>
        Carregando dados...
      </div>
    );
  }

  const historico = data?.historico || [];
  const regimeConfidence = historico.slice(-1)[0]?.score || 0;
  const regimeAtual = historico.slice(-1)[0]?.regime || "DESCONHECIDO";
  const sizingAtual = historico.slice(-1)[0]?.sizing || 0;

  let ciclosConsecutivos = 0;
  for (let i = historico.length - 1; i >= 0; i--) {
    if (historico[i].regime === regimeAtual) ciclosConsecutivos++;
    else break;
  }

  const timeline = historico.slice(-12).map((h) => ({
    regime: h.regime,
    ciclo: h.ciclo_id,
    data: h.timestamp?.slice(0, 10),
    sizing: h.sizing || 0,
    ir: h.ir || 0
  }));

  const transicoes = {};
  for (let i = 1; i < historico.length; i++) {
    const de = historico[i-1].regime;
    const para = historico[i].regime;
    if (de !== para) {
      const key = `${de} → ${para}`;
      transicoes[key] = (transicoes[key] || 0) + 1;
    }
  }

  const transicoesOrdenadas = Object.entries(transicoes)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  const distribuicao = {};
  historico.forEach((h) => {
    const regime = h.regime;
    distribuicao[regime] = (distribuicao[regime] || 0) + 1;
  });

  const totalCiclos = historico.length;
  const distribuicaoPercentual = Object.entries(distribuicao)
    .map(([regime, count]) => ({
      regime,
      count,
      percentual: totalCiclos > 0 ? ((count / totalCiclos) * 100).toFixed(1) : 0
    }))
    .sort((a, b) => b.count - a.count);

  const regimeMaisFrequente = distribuicaoPercentual[0]?.regime || "—";
  const countRegimeMaisFrequente = distribuicaoPercentual[0]?.count || 0;

  // getRegimeColor e getRegimeBgColor importados de ../store/regimeColors

  return (
    <div style={{ fontFamily: "monospace", fontSize: 11, display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Cards Principais */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Regime Atual</div>
          <div style={{ fontSize: 14, fontWeight: "bold", color: getRegimeColor(regimeAtual) }}>
            {regimeAtual}
          </div>
        </div>
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Confiança</div>
          <div style={{ fontSize: 14, fontWeight: "bold", color: regimeConfidence > 0.7 ? "var(--atlas-green)" : "var(--atlas-amber)" }}>
            {Math.abs(regimeConfidence * 100).toFixed(1)}%
          </div>
        </div>
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Ciclos Consecutivos</div>
          <div style={{ fontSize: 14, fontWeight: "bold" }}>{ciclosConsecutivos}</div>
        </div>
      </div>

      {/* Timeline Visual */}
      <div>
        <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>Timeline de Regimes (Últimos 12 Ciclos)</h4>
        {/* Rótulos YYYY-MM (linha superior, cinza neutro) */}
        <div style={{ display: "flex", gap: 4, overflowX: "auto", marginBottom: 4 }}>
          {timeline.map((t, i) => (
            <div key={i} style={{ minWidth: 70, textAlign: "center" }}>
              <div style={{ fontSize: 9, fontWeight: "bold", color: "var(--atlas-text-secondary)" }}>
                {t.ciclo || "—"}
              </div>
            </div>
          ))}
        </div>
        {/* Boxes coloridos (linha inferior) */}
        <div style={{ display: "flex", gap: 4, overflowX: "auto", paddingBottom: 8 }}>
          {timeline.map((t, i) => (
            <div 
              key={i} 
              style={{
                minWidth: 70,
                padding: "8px 6px",
                background: t.regime === regimeAtual ? getRegimeColor(t.regime) : getRegimeBgColor(t.regime),
                border: `2px solid ${t.regime === regimeAtual ? getRegimeColor(t.regime) : "var(--atlas-border)"}`,
                borderRadius: 4,
                textAlign: "center",
                opacity: t.sizing === 1 ? 1 : 0.7
              }}
            >
              <div style={{ fontSize: 9, fontWeight: "bold", color: t.regime === regimeAtual ? "#fff" : "var(--atlas-text-primary)" }}>{t.regime?.slice(0, 10)}</div>
              <div style={{ fontSize: 8, marginTop: 2, color: t.sizing === 1 ? "var(--atlas-green)" : "var(--atlas-text-secondary)" }}>{t.sizing === 1 ? "● ON" : "○ OFF"}</div>
              <div style={{ fontSize: 8, marginTop: 1, color: t.ir > 0 ? "var(--atlas-green)" : t.ir < 0 ? "var(--atlas-red)" : "var(--atlas-text-secondary)" }}>IR: {t.ir?.toFixed(2)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Distribuição e Regime Mais Frequente */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        <div>
          <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>Distribuição Histórica</h4>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {distribuicaoPercentual.map((d, i) => (
              <div 
                key={i} 
                style={{
                  padding: "8px 12px",
                  background: getRegimeBgColor(d.regime),
                  border: `1px solid ${getRegimeColor(d.regime)}`,
                  borderRadius: 4,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center"
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: getRegimeColor(d.regime) }} />
                  <span style={{ fontWeight: "bold", color: "var(--atlas-text-primary)" }}>{d.regime}</span>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ color: "var(--atlas-text-primary)", fontWeight: "bold" }}>{d.count} ciclos</div>
                  <div style={{ fontSize: 10, color: "var(--atlas-text-secondary)" }}>{d.percentual}%</div>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div>
          <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>Regime Mais Frequente</h4>
          <div style={{ 
            padding: 16, 
            background: getRegimeBgColor(regimeMaisFrequente),
            border: `2px solid ${getRegimeColor(regimeMaisFrequente)}`,
            borderRadius: 6,
            textAlign: "center"
          }}>
            <div style={{ fontSize: 18, fontWeight: "bold", color: getRegimeColor(regimeMaisFrequente) }}>{regimeMaisFrequente}</div>
            <div style={{ fontSize: 12, color: "var(--atlas-text-secondary)", marginTop: 4 }}>{countRegimeMaisFrequente} ciclos ({distribuicaoPercentual[0]?.percentual}%)</div>
          </div>
          <div style={{ marginTop: 16 }}>
            <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>Total de Ciclos</h4>
            <div style={{ 
              padding: 12, 
              background: "var(--atlas-surface)",
              border: "1px solid var(--atlas-border)",
              borderRadius: 4,
              textAlign: "center",
              fontSize: 20,
              fontWeight: "bold"
            }}>{totalCiclos}</div>
          </div>
        </div>
      </div>

      {/* Transições */}
      <div>
        <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>Transições Mais Frequentes</h4>
        {transicoesOrdenadas.length > 0 ? (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {transicoesOrdenadas.map(([transicao, count], i) => {
              const [de, para] = transicao.split(" → ");
              return (
                <div 
                  key={i} 
                  style={{
                    padding: "8px 12px",
                    background: "var(--atlas-surface)",
                    border: `1px solid ${getRegimeColor(para)}`,
                    borderRadius: 4,
                    fontSize: 10,
                    display: "flex",
                    alignItems: "center",
                    gap: 8
                  }}
                >
                  <span style={{ color: getRegimeColor(de) }}>{de}</span>
                  <span style={{ color: "var(--atlas-text-secondary)" }}>→</span>
                  <span style={{ color: getRegimeColor(para), fontWeight: "bold" }}>{para}</span>
                  <span style={{ background: "var(--atlas-blue)", color: "#fff", padding: "2px 6px", borderRadius: 2, fontSize: 9 }}>{count}x</span>
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{ padding: 12, color: "var(--atlas-text-secondary)", textAlign: "center", border: "1px dashed var(--atlas-border)", borderRadius: 4 }}>Sem transições registradas</div>
        )}
      </div>

      {/* Legenda */}
      <div style={{ padding: 8, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", borderRadius: 4, fontSize: 9, display: "flex", gap: 16, flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--atlas-green)" }} />
          <span>ALTA/BULL</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--atlas-red)" }} />
          <span>BAIXA/BEAR</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--atlas-blue)" }} />
          <span>LATERAL</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--atlas-amber)" }} />
          <span>TRANSIÇÃO</span>
        </div>
      </div>
    </div>
  );
};

// === SUB-ABA: REFLECT ===
const ReflectTab = ({ ticker, data }) => {
  const reflectHistorico = data?.reflect_historico || [];
  const reflectPermanentBlock = data?.reflect_permanent_block || false;
  const reflectStateAtual = data?.reflect_state || "B";

  // Deriva estado A/B/C/D a partir do score quando reflect_state por ciclo não está disponível
  const scoreToState = (score) => {
    if (score === null || score === undefined) return null;
    if (score >= 0.5)  return "A";
    if (score >= 0.0)  return "B";
    if (score >= -0.5) return "C";
    return "D";
  };

  const getStateColor = (state) => {
    if (!state) return "var(--atlas-text-secondary)";
    const s = state.toUpperCase();
    if (s === "A") return "var(--atlas-green)";
    if (s === "B") return "var(--atlas-blue)";
    if (s === "C") return "var(--atlas-amber)";
    if (s === "D") return "var(--atlas-red)";
    if (s === "E") return "var(--atlas-text-secondary)";
    return "var(--atlas-text-secondary)";
  };

  const getStateBgColor = (state) => {
    if (!state) return "var(--atlas-surface)";
    const s = state.toUpperCase();
    if (s === "A") return "rgba(34, 197, 94, 0.2)";
    if (s === "B") return "rgba(59, 130, 246, 0.2)";
    if (s === "C") return "rgba(245, 158, 11, 0.2)";
    if (s === "D") return "rgba(239, 68, 68, 0.2)";
    if (s === "E") return "rgba(100, 100, 100, 0.2)";
    return "var(--atlas-surface)";
  };

  const getStateTooltip = (state) => {
    const tooltips = {
      A: "Edge forte — aceleração positiva, delta IR positivo. Sizing pleno.",
      B: "Edge normal — condições dentro do esperado. Sizing padrão.",
      C: "Edge enfraquecendo — atenção. Sizing reduzido.",
      D: "Edge deteriorado — risco elevado. Sizing mínimo ou zero.",
      E: "Bloqueio — edge inválido. Sem operação até protocolo de 5 gates."
    };
    return tooltips[state?.toUpperCase()] || "Estado desconhecido";
  };

  return (
    <div style={{ fontFamily: "monospace", fontSize: 11, display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Cards de Resumo */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Estado Atual</div>
          <div style={{ fontSize: 18, fontWeight: "bold", color: getStateColor(reflectStateAtual) }}>
            {reflectStateAtual}
          </div>
        </div>
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Score Atual</div>
          <div style={{ fontSize: 18, fontWeight: "bold", color: reflectHistorico.slice(-1)[0]?.reflect_score > 0 ? "var(--atlas-green)" : "var(--atlas-amber)" }}>
            {reflectHistorico.slice(-1)[0]?.reflect_score != null
              ? reflectHistorico.slice(-1)[0].reflect_score.toFixed(4)
              : "—"}
          </div>
        </div>
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Bloqueio Permanente</div>
          <div style={{ fontSize: 18, fontWeight: "bold", color: reflectPermanentBlock ? "var(--atlas-red)" : "var(--atlas-green)" }}>
            {reflectPermanentBlock ? "SIM ⚠️" : "NÃO"}
          </div>
        </div>
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Total Ciclos REFLECT</div>
          <div style={{ fontSize: 18, fontWeight: "bold" }}>{reflectHistorico.length}</div>
        </div>
      </div>

      {/* Tabela Histórica */}
      <div>
        <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>Histórico de Ciclos REFLECT</h4>
        {reflectHistorico.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: "var(--atlas-text-secondary)", border: "1px dashed var(--atlas-border)", borderRadius: 4 }}>
            Nenhum dado REFLECT disponível
          </div>
        ) : (
          <div style={{ maxHeight: 400, overflowY: "auto", border: "1px solid var(--atlas-border)", borderRadius: 4 }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 10 }}>
              <thead style={{ position: "sticky", top: 0, background: "var(--atlas-bg)" }}>
                <tr style={{ borderBottom: "2px solid var(--atlas-border)" }}>
                  <th style={{ padding: 8, textAlign: "left" }}>Ciclo</th>
                  <th style={{ padding: 8, textAlign: "center" }}>Estado</th>
                  <th style={{ padding: 8, textAlign: "center" }}>Score</th>
                  <th style={{ padding: 8, textAlign: "center" }}>Aceleração</th>
                  <th style={{ padding: 8, textAlign: "center" }}>Delta IR</th>
                  <th style={{ padding: 8, textAlign: "center" }}>IV/Prêmio</th>
                  <th style={{ padding: 8, textAlign: "center" }}>Ret/Vol</th>
                </tr>
              </thead>
              <tbody>
                {reflectHistorico.slice().reverse().map((ciclo, i) => {
                  const state = ciclo.reflect_state || scoreToState(ciclo.reflect_score);
                  return (
                  <tr 
                    key={i} 
                    style={{ 
                      borderBottom: "1px solid var(--atlas-border)",
                      background: getStateBgColor(state),
                      opacity: state === "E" ? 0.6 : 1
                    }}
                    title={getStateTooltip(state)}
                  >
                    <td style={{ padding: 8, fontWeight: "bold" }}>{ciclo.ciclo_id || "—"}</td>
                    <td style={{ padding: 8, textAlign: "center" }}>
                      <span style={{ padding: "2px 8px", borderRadius: 2, fontSize: 9, background: getStateColor(state), color: "#fff", fontWeight: "bold" }}>
                        {state || "—"}
                      </span>
                    </td>
                    <td style={{ padding: 8, textAlign: "center" }}>
                      <div style={{ color: ciclo.reflect_score > 0 ? "var(--atlas-green)" : ciclo.reflect_score < 0 ? "var(--atlas-red)" : "var(--atlas-amber)", fontWeight: "bold" }}>
                        {ciclo.reflect_score != null ? ciclo.reflect_score.toFixed(4) : "—"}
                      </div>
                    </td>
                    <td style={{ padding: 8, textAlign: "center" }}>
                      <div style={{ color: ciclo.aceleracao > 0 ? "var(--atlas-green)" : ciclo.aceleracao < 0 ? "var(--atlas-red)" : "var(--atlas-text-secondary)", fontWeight: "bold" }}>
                        {ciclo.aceleracao?.toFixed(4) ?? "—"}
                      </div>
                    </td>
                    <td style={{ padding: 8, textAlign: "center" }}>
                      <div style={{ color: ciclo.delta_ir > 0 ? "var(--atlas-green)" : ciclo.delta_ir < 0 ? "var(--atlas-red)" : "var(--atlas-text-secondary)", fontWeight: "bold" }}>
                        {ciclo.delta_ir?.toFixed(4) ?? "—"}
                      </div>
                    </td>
                    <td style={{ padding: 8, textAlign: "center", color: "var(--atlas-text-secondary)" }}>
                      {ciclo.iv_prem_ratio != null ? ciclo.iv_prem_ratio.toFixed(4) : "—"}
                    </td>
                    <td style={{ padding: 8, textAlign: "center", color: "var(--atlas-text-secondary)" }}>
                      {ciclo.ret_vol_ratio != null ? ciclo.ret_vol_ratio.toFixed(4) : "—"}
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Legenda de Estados */}
      <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", borderRadius: 4, fontSize: 9 }}>
        <div style={{ marginBottom: 8, fontWeight: "bold", color: "var(--atlas-text-primary)" }}>Legenda de Estados REFLECT:</div>
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 12, height: 12, borderRadius: "50%", background: "var(--atlas-green)" }} />
            <span><strong>A:</strong> Edge forte</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 12, height: 12, borderRadius: "50%", background: "var(--atlas-blue)" }} />
            <span><strong>B:</strong> Edge normal</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 12, height: 12, borderRadius: "50%", background: "var(--atlas-amber)" }} />
            <span><strong>C:</strong> Edge enfraquecendo</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 12, height: 12, borderRadius: "50%", background: "var(--atlas-red)" }} />
            <span><strong>D:</strong> Edge deteriorado</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 12, height: 12, borderRadius: "50%", background: "var(--atlas-text-secondary)" }} />
            <span><strong>E:</strong> Bloqueio</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// === SUB-ABA: CICLOS ===
const CiclosTab = ({ ticker, data }) => {
  const [filtro, setFiltro] = useState("todos");
  const [filtroRegime, setFiltroRegime] = useState("todos");
  const historico = data?.historico || [];
  const ciclosExecutados = historico.filter(h => h.sizing === 1);
  const ciclosRejeitados = historico.filter(h => h.sizing === 0);
  
  let ciclosFiltrados = historico;
  if (filtro === "executados") ciclosFiltrados = ciclosExecutados;
  if (filtro === "rejeitados") ciclosFiltrados = ciclosRejeitados;
  if (filtroRegime !== "todos") {
    ciclosFiltrados = ciclosFiltrados.filter(h => h.regime === filtroRegime);
  }

  const totalCiclos = historico.length;
  const totalExecutados = ciclosExecutados.length;
  const totalRejeitados = ciclosRejeitados.length;
  const taxaExecucao = totalCiclos > 0 ? ((totalExecutados / totalCiclos) * 100).toFixed(1) : 0;
  const irMedioExecutados = ciclosExecutados.length > 0
    ? (ciclosExecutados.reduce((sum, h) => sum + (h.ir || 0), 0) / ciclosExecutados.length).toFixed(3)
    : 0;
  const winsExecutados = ciclosExecutados.filter(h => h.ir > 0).length;
  const winRate = ciclosExecutados.length > 0
    ? ((winsExecutados / ciclosExecutados.length) * 100).toFixed(1)
    : 0;
  const regimesUnicos = [...new Set(historico.map(h => h.regime))].filter(Boolean);

  const getRegimeColor = (regime) => {
    if (!regime) return "var(--atlas-text-secondary)";
    const r = regime.toUpperCase();
    if (r.includes("ALTA") || r.includes("BULL")) return "var(--atlas-green)";
    if (r.includes("BAIXA") || r.includes("BEAR")) return "var(--atlas-red)";
    if (r.includes("TRANSICAO") || r.includes("TRANSIÇÃO")) return "var(--atlas-amber)";
    if (r.includes("LATERAL")) return "var(--atlas-blue)";
    return "var(--atlas-text-secondary)";
  };

  return (
    <div style={{ fontFamily: "monospace", fontSize: 11, display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Nota A07 */}
      <div style={{
        padding: "6px 12px",
        background: "rgba(59,130,246,0.1)",
        border: "1px solid var(--atlas-blue)",
        borderRadius: 2,
        fontFamily: "monospace",
        fontSize: 10,
        marginBottom: 12,
        color: "var(--atlas-text-secondary)"
      }}>
        HISTÓRICO DE CICLOS ORBIT — dados de backtest histórico do classificador de regime.
        Operações paper trading reais estão em Visão Geral → Posições Abertas.
      </div>

      {/* Cards de Estatísticas */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Total de Ciclos</div>
          <div style={{ fontSize: 18, fontWeight: "bold" }}>{totalCiclos}</div>
        </div>
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Executados</div>
          <div style={{ fontSize: 18, fontWeight: "bold", color: "var(--atlas-green)" }}>
            {totalExecutados} ({taxaExecucao}%)
          </div>
        </div>
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Rejeitados (GATE)</div>
          <div style={{ fontSize: 18, fontWeight: "bold", color: "var(--atlas-red)" }}>{totalRejeitados}</div>
        </div>
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Win Rate</div>
          <div style={{ fontSize: 18, fontWeight: "bold", color: winRate > 50 ? "var(--atlas-green)" : "var(--atlas-amber)" }}>
            {winRate}%
          </div>
          <div style={{ fontSize: 9, color: "var(--atlas-text-secondary)", marginTop: 2 }}>
            IR Médio: {irMedioExecutados}
          </div>
        </div>
      </div>

      {/* Filtros */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <div style={{ color: "var(--atlas-text-secondary)", fontSize: 10 }}>Filtrar: </div>
        <select value={filtro} onChange={(e) => setFiltro(e.target.value)} style={{ background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", color: "var(--atlas-text-primary)", fontFamily: "monospace", fontSize: 10, padding: "4px 8px" }}>
          <option value="todos">Todos os Ciclos</option>
          <option value="executados">Executados (ON)</option>
          <option value="rejeitados">Rejeitados (OFF)</option>
        </select>
        <select value={filtroRegime} onChange={(e) => setFiltroRegime(e.target.value)} style={{ background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", color: "var(--atlas-text-primary)", fontFamily: "monospace", fontSize: 10, padding: "4px 8px" }}>
          <option value="todos">Todos os Regimes</option>
          {regimesUnicos.map(regime => (
            <option key={regime} value={regime}>{regime}</option>
          ))}
        </select>
        <div style={{ flex: 1 }} />
        <div style={{ fontSize: 10, color: "var(--atlas-text-secondary)" }}>
          Mostrando {ciclosFiltrados.length} de {totalCiclos} ciclos
        </div>
      </div>

      {/* Tabela de Ciclos */}
      <div>
        <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>Histórico de Ciclos</h4>
        {ciclosFiltrados.length === 0 ? (
          <div style={{ padding: 20, textAlign: "center", color: "var(--atlas-text-secondary)", border: "1px dashed var(--atlas-border)", borderRadius: 4 }}>
            Nenhum ciclo encontrado com os filtros selecionados
          </div>
        ) : (
          <div style={{ maxHeight: 400, overflowY: "auto", border: "1px solid var(--atlas-border)", borderRadius: 4 }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 10 }}>
              <thead style={{ position: "sticky", top: 0, background: "var(--atlas-bg)" }}>
                <tr style={{ borderBottom: "2px solid var(--atlas-border)" }}>
                  <th style={{ padding: 8, textAlign: "left" }}>Ciclo</th>
                  <th style={{ padding: 8, textAlign: "left" }}>Data</th>
                  <th style={{ padding: 8, textAlign: "left" }}>Regime</th>
                  <th style={{ padding: 8, textAlign: "center" }}>Status</th>
                  <th style={{ padding: 8, textAlign: "center" }}>Confiança</th>
                  <th style={{ padding: 8, textAlign: "center" }}>IR</th>
                  <th style={{ padding: 8, textAlign: "center" }}>IR Treino</th>
                  <th style={{ padding: 8, textAlign: "center" }}>Vol 21d</th>
                </tr>
              </thead>
              <tbody>
                {ciclosFiltrados.slice().reverse().map((ciclo, i) => {
                  const isExecutado = ciclo.sizing === 1;
                  const scorePct = (ciclo.score || 0) * 100;
                  const irValue = ciclo.ir || 0;
                  const irTreino = ciclo.ir_treino || 0;
                  return (
                    <tr key={i} style={{ borderBottom: "1px solid var(--atlas-border)", background: isExecutado ? "rgba(34, 197, 94, 0.05)" : "rgba(239, 68, 68, 0.05)", opacity: isExecutado ? 1 : 0.7 }}>
                      <td style={{ padding: 8, fontWeight: "bold" }}>{ciclo.ciclo_id || "—"}</td>
                      <td style={{ padding: 8, color: "var(--atlas-text-secondary)" }}>{ciclo.data_ref?.slice(0, 10) || ciclo.timestamp?.slice(0, 10) || "—"}</td>
                      <td style={{ padding: 8, color: getRegimeColor(ciclo.regime) }}>{ciclo.regime || "—"}</td>
                      <td style={{ padding: 8, textAlign: "center" }}>
                        <span style={{ padding: "2px 8px", borderRadius: 2, fontSize: 9, background: isExecutado ? "var(--atlas-green)" : "var(--atlas-red)", color: "#fff" }}>
                          {isExecutado ? "ON" : "OFF"}
                        </span>
                      </td>
                      <td style={{ padding: 8, textAlign: "center" }}>
                        <div style={{ color: scorePct > 70 ? "var(--atlas-green)" : scorePct > 40 ? "var(--atlas-amber)" : "var(--atlas-red)" }}>
                          {scorePct.toFixed(1)}%
                        </div>
                        <div style={{ fontSize: 8, color: "var(--atlas-text-secondary)" }}>
                          thresh: {(ciclo.thresh || 0).toFixed(3)}
                        </div>
                      </td>
                      <td style={{ padding: 8, textAlign: "center" }}>
                        <div style={{ color: irValue > 0 ? "var(--atlas-green)" : irValue < 0 ? "var(--atlas-red)" : "var(--atlas-text-secondary)", fontWeight: "bold" }}>
                          {irValue.toFixed(3)}
                        </div>
                      </td>
                      <td style={{ padding: 8, textAlign: "center", color: "var(--atlas-text-secondary)" }}>{irTreino.toFixed(3)}</td>
                      <td style={{ padding: 8, textAlign: "center", color: "var(--atlas-text-secondary)" }}>{(ciclo.vol_21d || 0).toFixed(3)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Resumo por Regime */}
      <div>
        <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>Performance por Regime</h4>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
          {regimesUnicos.map(regime => {
            const ciclosNoRegime = historico.filter(h => h.regime === regime);
            const executadosNoRegime = ciclosNoRegime.filter(h => h.sizing === 1);
            const irMedioRegime = executadosNoRegime.length > 0
              ? (executadosNoRegime.reduce((sum, h) => sum + (h.ir || 0), 0) / executadosNoRegime.length).toFixed(3)
              : 0;
            const winRateRegime = executadosNoRegime.length > 0
              ? ((executadosNoRegime.filter(h => h.ir > 0).length / executadosNoRegime.length) * 100).toFixed(1)
              : 0;
            return (
              <div key={regime} style={{ padding: 12, background: "var(--atlas-surface)", border: `2px solid ${getRegimeColor(regime)}`, borderRadius: 4 }}>
                <div style={{ color: getRegimeColor(regime), fontWeight: "bold", marginBottom: 8 }}>{regime}</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 8, fontSize: 10 }}>
                  <div>
                    <div style={{ color: "var(--atlas-text-secondary)" }}>Ciclos</div>
                    <div style={{ fontWeight: "bold" }}>{ciclosNoRegime.length}</div>
                  </div>
                  <div>
                    <div style={{ color: "var(--atlas-text-secondary)" }}>Executados</div>
                    <div style={{ fontWeight: "bold" }}>{executadosNoRegime.length}</div>
                  </div>
                  <div>
                    <div style={{ color: "var(--atlas-text-secondary)" }}>IR Médio</div>
                    <div style={{ fontWeight: "bold", color: irMedioRegime > 0 ? "var(--atlas-green)" : "var(--atlas-red)" }}>{irMedioRegime}</div>
                  </div>
                  <div>
                    <div style={{ color: "var(--atlas-text-secondary)" }}>Win Rate</div>
                    <div style={{ fontWeight: "bold", color: winRateRegime > 50 ? "var(--atlas-green)" : "var(--atlas-amber)" }}>{winRateRegime}%</div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// === SUB-ABA: ANALYTICS (COM TOOLTIPS B04) ===
const AnalyticsTab = ({ ticker, data, analytics }) => {
  const [localAnalytics, setLocalAnalytics] = useState(null);
  const [timeRange, setTimeRange] = useState("all");
  const historico = data?.historico || [];

  useEffect(() => {
    if (localAnalytics) return;
    async function fetchAnalytics() {
      try {
        const res = await fetch(`${API_BASE}/ativos/${ticker}/analytics`);
        if (res.ok) {
          const analyticsData = await res.json();
          setLocalAnalytics({
            ticker: analyticsData.ticker,
            ohlcv_disponivel: analyticsData.ohlcv_disponivel,
            walkForward: analyticsData.walk_forward,
            fatTails: analyticsData.fat_tails,
            distribution: analyticsData.distribution,
            acf: analyticsData.acf,
            gateThreshold: analyticsData.gate_threshold || 0.18,
          });
        }
      } catch (err) {
        console.warn("Erro ao buscar analytics:", err.message);
      }
    }
    fetchAnalytics();
  }, [ticker]);

  const effectiveAnalytics = localAnalytics || analytics;
  const [threshold, setThreshold] = useState(effectiveAnalytics?.gateThreshold || 0.18);
  const irValues = historico.map(h => h.ir || 0).filter(v => v !== 0);
  const irSorted = [...irValues].sort((a, b) => a - b);
  const estatisticasIR = {
    media: irValues.length > 0 ? (irValues.reduce((a, b) => a + b, 0) / irValues.length).toFixed(3) : 0,
    mediana: irSorted.length > 0 ? irSorted[Math.floor(irSorted.length / 2)].toFixed(3) : 0,
    p1: irSorted.length > 0 ? irSorted[Math.floor(irSorted.length * 0.01)].toFixed(3) : 0,
    p99: irSorted.length > 0 ? irSorted[Math.floor(irSorted.length * 0.99)].toFixed(3) : 0,
    std: irValues.length > 1
      ? Math.sqrt(irValues.reduce((sum, v) => sum + Math.pow(v - (irValues.reduce((a,b)=>a+b,0)/irValues.length), 2), 0) / (irValues.length - 1)).toFixed(3)
      : 0,
    min: irSorted[0]?.toFixed(3) || 0,
    max: irSorted[irSorted.length - 1]?.toFixed(3) || 0,
    total: irValues.length
  };
  
  const tradesComThreshold = historico.filter(h => (h.score || 0) >= threshold);
  const irComThreshold = tradesComThreshold.map(h => h.ir || 0).filter(v => v !== 0);
  const irMedioThreshold = irComThreshold.length > 0
    ? (irComThreshold.reduce((a, b) => a + b, 0) / irComThreshold.length).toFixed(3)
    : 0;
  const winRateThreshold = irComThreshold.length > 0
    ? ((irComThreshold.filter(v => v > 0).length / irComThreshold.length) * 100).toFixed(1)
    : 0;
  
  const faixasIR = [
    { label: "IR < -0.5", min: -Infinity, max: -0.5, count: 0, color: "var(--atlas-red)" },
    { label: "-0.5 a -0.2", min: -0.5, max: -0.2, count: 0, color: "var(--atlas-red)" },
    { label: "-0.2 a 0", min: -0.2, max: 0, count: 0, color: "var(--atlas-amber)" },
    { label: "0 a 0.2", min: 0, max: 0.2, count: 0, color: "var(--atlas-amber)" },
    { label: "0.2 a 0.5", min: 0.2, max: 0.5, count: 0, color: "var(--atlas-green)" },
    { label: "IR > 0.5", min: 0.5, max: Infinity, count: 0, color: "var(--atlas-green)" },
  ];
  
  irValues.forEach(ir => {
    faixasIR.forEach(faixa => {
      if (ir >= faixa.min && ir < faixa.max) {
        faixa.count++;
      }
    });
  });

  const getValueColor = (value, positive = true) => {
    const v = parseFloat(value);
    if (positive) {
      if (v > 0) return "var(--atlas-green)";
      if (v < 0) return "var(--atlas-red)";
      return "var(--atlas-text-secondary)";
    }
    return "var(--atlas-text-primary)";
  };

  const fonteHistorico = (
    <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-blue)", marginBottom: 12, marginTop: -8 }}>
      fonte: campo 'ir' em historico[] — {ticker}.json
    </div>
  );
  
  const fonteOhlcv = (
    <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-blue)", marginBottom: 12, marginTop: -8 }}>
      fonte: TAPE/ohlcv/{ticker}.parquet — retorno diário
    </div>
  );

  return (
    <div style={{ fontFamily: "monospace", fontSize: 11, display: "flex", flexDirection: "column", gap: 24 }}>
      {/* Controles */}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
        <label style={{ color: "var(--atlas-text-secondary)", display: "block", marginBottom: 4 }}>
          Threshold do GATE
          <input type="range" min="0" max="1" step="0.01" value={threshold} onChange={(e) => setThreshold(parseFloat(e.target.value))} style={{ width: 200 }} />
          <div style={{ fontSize: 10, color: "var(--atlas-text-primary)", marginTop: 2 }}>{threshold.toFixed(2)}</div>
        </label>
        <div>
          <label style={{ color: "var(--atlas-text-secondary)", display: "block", marginBottom: 4 }}>Período</label>
          <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)} style={{ background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", color: "var(--atlas-text-primary)", fontFamily: "monospace", fontSize: 10, padding: "4px 8px" }}>
            <option value="all">Todos os Ciclos</option>
            <option value="12m">Últimos 12 meses</option>
            <option value="6m">Últimos 6 meses</option>
            <option value="3m">Últimos 3 meses</option>
          </select>
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ fontSize: 10, color: "var(--atlas-text-secondary)" }}>
          Com threshold {threshold.toFixed(2)}: {tradesComThreshold.length} trades selecionados
        </div>
      </div>

      {/* BLOCO 1 — MÉTRICAS DO IR */}
      <div style={{ border: "1px solid var(--atlas-border)", borderRadius: 4, padding: 16, background: "var(--atlas-bg)" }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "var(--atlas-text-secondary)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 4 }}>
          MÉTRICAS DO IR
        </div>
        <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-blue)", marginBottom: 16 }}>
          fonte: campo 'ir' em historico[] — {ticker}.json
        </div>

        {/* Cards de Estatísticas IR */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 24 }}>
          <Tooltip content={
            <div style={{ lineHeight: 1.6 }}>
              <div><strong>P1% — CAUDA ESQUERDA</strong></div>
              <div style={{ marginTop: 4 }}>Fonte: retornos diários do arquivo OHLCV</div>
              <div style={{ marginTop: 4 }}>O quê: retorno do pior 1% dos dias históricos deste ativo.</div>
              <div style={{ marginTop: 4 }}>Exemplo: P1% = -4,2% significa que 1% dos dias históricos tiveram retorno pior que -4,2%.</div>
              <div style={{ marginTop: 6, color: "var(--atlas-amber)" }}>Como usar para vendedor de vol: Dimensiona o evento de cauda real deste ativo. Se o stop da estratégia está acima do P1% em valor absoluto, o sistema sobrevive ao evento histórico mais extremo. Se está abaixo, não.</div>
            </div>
          } position="top" delay={600}>
            <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", cursor: "help" }}>
              <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>P1% (Cauda Esquerda)</div>
              <div style={{ fontSize: 16, fontWeight: "bold", color: getValueColor(estatisticasIR.p1, false) }}>{estatisticasIR.p1}</div>
            </div>
          </Tooltip>

          <Tooltip content={
            <div style={{ lineHeight: 1.6 }}>
              <div><strong>P99% — CAUDA DIREITA</strong></div>
              <div style={{ marginTop: 4 }}>Fonte: retornos diários do arquivo OHLCV</div>
              <div style={{ marginTop: 4 }}>O quê: retorno do melhor 1% dos dias históricos.</div>
              <div style={{ marginTop: 6, color: "var(--atlas-amber)" }}>Como usar: Referência secundária para vendedor de vol. Mais relevante para estratégias direcionais long.</div>
            </div>
          } position="top" delay={600}>
            <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", cursor: "help" }}>
              <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>P99% (Cauda Direita)</div>
              <div style={{ fontSize: 16, fontWeight: "bold", color: getValueColor(estatisticasIR.p99) }}>{estatisticasIR.p99}</div>
            </div>
          </Tooltip>

          <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
            <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>IR Médio (com threshold)</div>
            <div style={{ fontSize: 16, fontWeight: "bold", color: getValueColor(irMedioThreshold) }}>{irMedioThreshold}</div>
          </div>

          <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
            <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Win Rate (com threshold)</div>
            <div style={{ fontSize: 16, fontWeight: "bold", color: winRateThreshold > 50 ? "var(--atlas-green)" : "var(--atlas-amber)" }}>{winRateThreshold}%</div>
          </div>
        </div>

        {/* Distribuição de IR */}
        <div style={{ marginBottom: 24 }}>
          <Tooltip content={
            <div style={{ lineHeight: 1.6 }}>
              <div><strong>DISTRIBUIÇÃO DE IR</strong></div>
              <div style={{ marginTop: 4 }}>Fonte: campo 'ir' do histórico ORBIT em {ticker}.json</div>
              <div style={{ marginTop: 4 }}>O quê: histograma de todos os IRs mensais históricos do sistema neste ativo.</div>
              <div style={{ marginTop: 4 }}>N: {estatisticasIR.total} ciclos mensais no histórico.</div>
              <div style={{ marginTop: 6 }}>Como usar:</div>
              <div style={{ marginLeft: 12, marginTop: 2 }}>• Maioria das barras à direita de zero = sistema consistentemente lucrativo neste ativo</div>
              <div style={{ marginLeft: 12, marginTop: 2 }}>• Barras à esquerda = ciclos com IR negativo</div>
              <div style={{ marginLeft: 12, marginTop: 2 }}>• Distribuição estreita = comportamento previsível</div>
              <div style={{ marginLeft: 12, marginTop: 2 }}>• Distribuição larga = alta variabilidade entre ciclos</div>
            </div>
          } position="top" delay={600}>
            <h4 style={{ marginBottom: 4, color: "var(--atlas-text-primary)", cursor: "help" }}>
              Distribuição de Information Ratio ⓘ
            </h4>
          </Tooltip>
          {fonteHistorico}

          <div style={{ display: "flex", gap: 16, marginBottom: 16, fontSize: 10 }}>
            <div style={{ color: "var(--atlas-red)" }}>
              <span style={{ fontWeight: "bold" }}>{faixasIR.slice(0, 3).reduce((sum, f) => sum + f.count, 0)}</span> negativos
            </div>
            <div style={{ color: "var(--atlas-amber)" }}>
              <span style={{ fontWeight: "bold" }}>{faixasIR.slice(3, 4).reduce((sum, f) => sum + f.count, 0)}</span> neutros
            </div>
            <div style={{ color: "var(--atlas-green)" }}>
              <span style={{ fontWeight: "bold" }}>{faixasIR.slice(4).reduce((sum, f) => sum + f.count, 0)}</span> positivos
            </div>
            <div style={{ color: "var(--atlas-text-secondary)", marginLeft: "auto" }}>
              Total: <span style={{ fontWeight: "bold" }}>{estatisticasIR.total}</span> ciclos
            </div>
          </div>

          <div style={{ padding: 24, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", borderRadius: 6 }}>
            <div style={{ display: "flex", alignItems: "flex-end", gap: 12, height: 200, paddingBottom: 40 }}>
              {faixasIR.map((faixa, i) => {
                const percentage = estatisticasIR.total > 0 ? ((faixa.count / estatisticasIR.total) * 100).toFixed(0) : 0;
                const barHeight = percentage * 2;
                return (
                  <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-end", height: "100%", position: "relative" }}>
                    <div style={{ width: "100%", height: `${Math.max(barHeight, 8)}%`, background: faixa.color, opacity: 0.85, borderRadius: "4px 4px 0 0", boxShadow: `0 -2px 8px ${faixa.color}40`, transition: "all 0.3s ease", position: "relative" }}>
                      {barHeight > 15 && (
                        <div style={{ position: "absolute", top: 8, left: "50%", transform: "translateX(-50%)", fontSize: 11, fontWeight: "bold", color: "#fff", textShadow: "0 1px 2px rgba(0,0,0,0.8)" }}>
                          {faixa.count}
                        </div>
                      )}
                    </div>
                    {barHeight <= 15 && (
                      <div style={{ fontSize: 11, fontWeight: "bold", color: faixa.color, marginBottom: 4, minHeight: 16 }}>{faixa.count}</div>
                    )}
                    <div style={{ fontSize: 9, color: "var(--atlas-text-secondary)", marginTop: 2 }}>{percentage}%</div>
                    <div style={{ position: "absolute", bottom: -36, left: "50%", transform: "translateX(-50%)", fontSize: 10, fontWeight: "500", color: faixa.color, textAlign: "center", whiteSpace: "nowrap" }}>
                      {faixa.label}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Estatísticas Detalhadas + Impacto do Threshold */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16, marginBottom: 24 }}>
          <div>
            <h4 style={{ marginBottom: 4, color: "var(--atlas-text-primary)" }}>Métricas Estatísticas</h4>
            {fonteHistorico}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 8 }}>
              {[
                { label: "Média", value: estatisticasIR.media },
                { label: "Mediana", value: estatisticasIR.mediana },
                { label: "Desvio Padrão", value: estatisticasIR.std },
                { label: "Mínimo", value: estatisticasIR.min },
                { label: "Máximo", value: estatisticasIR.max },
                { label: "Total Ciclos", value: estatisticasIR.total },
              ].map((stat, i) => (
                <div key={i} style={{ padding: 8, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", borderRadius: 2 }}>
                  <div style={{ color: "var(--atlas-text-secondary)", fontSize: 9 }}>{stat.label}</div>
                  <div style={{ fontWeight: "bold", color: getValueColor(stat.value) }}>{stat.value}</div>
                </div>
              ))}
            </div>
          </div>

          <Tooltip content={
            <div style={{ lineHeight: 1.6 }}>
              <div><strong>SIMULADOR DE THRESHOLD</strong></div>
              <div style={{ marginTop: 4 }}>O quê: ferramenta de simulação — mostra como o IR médio e o win rate mudariam se apenas ciclos com score ORBIT acima de X fossem operados.</div>
              <div style={{ marginTop: 4, color: "var(--atlas-amber)" }}>Threshold atual do GATE no sistema: 0.60 (hardcoded).</div>
              <div style={{ marginTop: 6, color: "var(--atlas-red)", fontWeight: "bold" }}>IMPORTANTE: este slider NÃO altera o threshold real do sistema. É apenas visualização de impacto.</div>
              <div style={{ marginTop: 6 }}>Para alterar o threshold operacional, editar o parâmetro 'thresh' na configuração do ativo via painel de edição.</div>
              <div style={{ marginTop: 6 }}>Como usar:</div>
              <div style={{ marginLeft: 12, marginTop: 2 }}>• Arraste para a direita = mais seletivo, menos trades</div>
              <div style={{ marginLeft: 12, marginTop: 2 }}>• Observe se o IR melhora sem reduzir N abaixo de 20 ciclos</div>
              <div style={{ marginLeft: 12, marginTop: 2 }}>• Ponto ideal: maior IR com N ainda estatisticamente válido</div>
            </div>
          } position="top" delay={600}>
            <div>
              <h4 style={{ marginBottom: 4, color: "var(--atlas-text-primary)", cursor: "help" }}>
                Impacto do Threshold ⓘ
              </h4>
              {fonteHistorico}
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", borderRadius: 4 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ color: "var(--atlas-text-secondary)" }}>Trades Selecionados</span>
                    <span style={{ fontWeight: "bold" }}>{tradesComThreshold.length} / {historico.length}</span>
                  </div>
                  <div style={{ height: 6, background: "var(--atlas-border)", borderRadius: 3, overflow: "hidden" }}>
                    <div style={{ width: `${(tradesComThreshold.length / Math.max(historico.length, 1)) * 100}%`, height: "100%", background: "var(--atlas-blue)", borderRadius: 3 }} />
                  </div>
                </div>
                <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", borderRadius: 4 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ color: "var(--atlas-text-secondary)" }}>IR Médio Filtrado</span>
                    <span style={{ fontWeight: "bold", color: getValueColor(irMedioThreshold) }}>{irMedioThreshold}</span>
                  </div>
                  <div style={{ fontSize: 9, color: "var(--atlas-text-secondary)" }}>vs. IR Geral: {estatisticasIR.media}</div>
                </div>
                <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", borderRadius: 4 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ color: "var(--atlas-text-secondary)" }}>Win Rate Filtrado</span>
                    <span style={{ fontWeight: "bold", color: winRateThreshold > 50 ? "var(--atlas-green)" : "var(--atlas-amber)" }}>{winRateThreshold}%</span>
                  </div>
                  <div style={{ fontSize: 9, color: "var(--atlas-text-secondary)" }}>Trades com IR &gt 0</div>
                </div>
              </div>
            </div>
          </Tooltip>
        </div>

        {/* Walk-Forward */}
        <Tooltip content={
          <div style={{ lineHeight: 1.6 }}>
            <div><strong>WALK-FORWARD IR</strong></div>
            <div style={{ marginTop: 4 }}>Fonte: campo 'ir' do histórico ORBIT em {ticker}.json</div>
            <div style={{ marginTop: 4 }}>O quê: IR médio calculado em janelas móveis de 12 ciclos mensais. Cada ponto representa a média dos últimos 12 ciclos.</div>
            <div style={{ marginTop: 6 }}>Como usar:</div>
            <div style={{ marginLeft: 12, marginTop: 2 }}>• IR acima de zero = edge positivo nessa janela</div>
            <div style={{ marginLeft: 12, marginTop: 2 }}>• Queda sustentada abaixo de zero = edge deteriorando</div>
            <div style={{ marginLeft: 12, marginTop: 2 }}>• Banda sombreada = incerteza estatística (IC 95%)</div>
            <div style={{ marginTop: 6 }}>Eixo X: ciclo do último mês da janela (ex: 2024-03)</div>
            <div>Eixo Y: Information Ratio médio da janela</div>
          </div>
        } position="top" delay={600}>
          <h4 style={{ marginBottom: 4, color: "var(--atlas-text-primary)", cursor: "help" }}>
            Walk-Forward Performance ⓘ
          </h4>
        </Tooltip>
        {fonteHistorico}
        {effectiveAnalytics?.walkForward ? (
          <WalkForwardChart data={effectiveAnalytics.walkForward} />
        ) : (
          <div style={{ padding: 40, textAlign: "center", color: "var(--atlas-text-secondary)", border: "1px dashed var(--atlas-border)", borderRadius: 4 }}>
            Dados de walk-forward não disponíveis
          </div>
        )}
      </div>

      {/* BLOCO 2 — MÉTRICAS DO ATIVO */}
      <div style={{ border: "1px solid var(--atlas-border)", borderRadius: 4, padding: 16, background: "var(--atlas-bg)" }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "var(--atlas-text-secondary)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 4 }}>
          MÉTRICAS DO ATIVO
        </div>
        <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-blue)", marginBottom: 16 }}>
          fonte: TAPE/ohlcv/{ticker}.parquet — retorno diário
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
          <div>
            <Tooltip content={
              <div style={{ lineHeight: 1.6 }}>
                <div><strong>DISTRIBUIÇÃO DE RETORNOS</strong></div>
                <div style={{ marginTop: 4 }}>Fonte: arquivo TAPE/ohlcv/{ticker}.parquet, coluna 'close'</div>
                <div style={{ marginTop: 4 }}>O quê: histograma dos retornos diários percentuais do ativo (não do sistema de trading).</div>
                <div style={{ marginTop: 4 }}>N: número de dias úteis com preço disponível no arquivo.</div>
                <div style={{ marginTop: 6 }}>Como usar:</div>
                <div style={{ marginLeft: 12, marginTop: 2 }}>• Forma da distribuição revela o comportamento real do ativo</div>
                <div style={{ marginLeft: 12, marginTop: 2 }}>• Caudas pesadas = risco de eventos extremos maior que o esperado por uma distribuição normal</div>
                <div style={{ marginLeft: 12, marginTop: 2 }}>• Assimetria para esquerda = quedas mais intensas que altas</div>
                <div style={{ marginTop: 6, color: "var(--atlas-red)", fontWeight: "bold" }}>Atenção: este gráfico mostra o ATIVO, não o IR do sistema.</div>
              </div>
            } position="top" delay={600}>
              <h4 style={{ marginBottom: 4, color: "var(--atlas-text-primary)", cursor: "help" }}>
                Distribuição de Retornos ⓘ
              </h4>
            </Tooltip>
            {fonteOhlcv}
            {effectiveAnalytics?.distribution ? (
              <DistributionChart data={effectiveAnalytics.distribution} />
            ) : (
              <div style={{ padding: 40, textAlign: "center", color: "var(--atlas-text-secondary)", border: "1px dashed var(--atlas-border)", borderRadius: 4 }}>
                Dados de distribuição não disponíveis
              </div>
            )}
          </div>

          <div>
            <h4 style={{ marginBottom: 4, color: "var(--atlas-text-primary)" }}>Autocorrelação (ACF)</h4>
            {fonteOhlcv}
            {effectiveAnalytics?.acf ? (
              <ACFChart data={effectiveAnalytics.acf} />
            ) : (
              <div style={{ padding: 40, textAlign: "center", color: "var(--atlas-text-secondary)", border: "1px dashed var(--atlas-border)", borderRadius: 4 }}>
                Dados de ACF não disponíveis
              </div>
            )}
          </div>

          <div>
            <h4 style={{ marginBottom: 4, color: "var(--atlas-text-primary)" }}>Caudas Pesadas (Fat Tails)</h4>
            {fonteOhlcv}
            {effectiveAnalytics?.fatTails ? (
              <TailMetrics data={effectiveAnalytics.fatTails} />
            ) : (
              <div style={{ padding: 40, textAlign: "center", color: "var(--atlas-text-secondary)", border: "1px dashed var(--atlas-border)", borderRadius: 4 }}>
                Dados de fat tails não disponíveis
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Legenda Geral */}
      <div style={{ padding: 8, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", borderRadius: 4, fontSize: 9, display: "flex", gap: 16, flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--atlas-green)" }} />
          <span>IR Positivo</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--atlas-red)" }} />
          <span>IR Negativo</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--atlas-amber)" }} />
          <span>IR Próximo de Zero</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <span style={{ color: "var(--atlas-blue)" }}>▮</span>
          <span>Barra de progresso = % de trades selecionados</span>
        </div>
      </div>
    </div>
  );
};

// === COMPONENTE PRINCIPAL ===
export default function AtivoView({ activeTicker, analytics, onTickerChange }) {
  const [subTab, setSubTab] = useState("orbit");
  const [data, setData] = useState(null);
  const [ativos, setAtivos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchAtivo() {
      if (!activeTicker) return;
      setLoading(true);
      setError(null);
      try {
        const resAtivos = await fetch(`${API_BASE}/ativos`);
        if (resAtivos.ok) {
          const dataAtivos = await resAtivos.json();
          setAtivos(dataAtivos.ativos || []);
        }
        const res = await fetch(`${API_BASE}/ativos/${activeTicker}`);
        if (!res.ok) throw new Error(`Erro HTTP: ${res.status}`);
        const json = await res.json();
        setData(json);
      } catch (err) {
        console.error("❌ Erro ao carregar ativo:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchAtivo();
  }, [activeTicker]);

  if (loading) return <div style={{ padding: 40, textAlign: "center", color: "var(--atlas-text-secondary)" }}>Carregando...</div>;
  if (error) return <div style={{ padding: 40, textAlign: "center", color: "var(--atlas-red)" }}>Erro: {error}</div>;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* NAV BAR — Dropdown e Tabs INLINE */}
      <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
        {/* Label + Dropdown — COM linha azul */}
        <div style={{ 
          display: "flex", 
          alignItems: "center", 
          gap: 8,
          borderBottom: "2px solid var(--atlas-blue)",
          paddingBottom: 8
        }}>
          <span style={{
            fontFamily: "monospace",
            fontSize: 13,
            fontWeight: "bold",
            color: "var(--atlas-text-primary)",
            textTransform: "uppercase"
          }}>
            ATIVO:
          </span>
          <select
            value={activeTicker || " "}
            onChange={(e) => onTickerChange && onTickerChange(e.target.value)}
            style={{
              padding: "8px 16px",
              background: "var(--atlas-surface)",
              border: "1px solid var(--atlas-border)",
              color: "var(--atlas-text-primary)",
              fontFamily: "monospace",
              fontSize: 13,
              fontWeight: "bold",
              borderRadius: 2,
              cursor: "pointer",
              minWidth: 140,
              textTransform: "uppercase"
            }}
          >
            <option value=" ">Selecione...</option>
            {ativos.map((ticker) => (
              <option key={ticker} value={ticker}>{ticker}</option>
            ))}
          </select>
        </div>

        {/* Tabs — SEM linha azul */}
        <div style={{ display: "flex", gap: 8 }}>
          {["orbit", "reflect", "ciclos", "analytics", "relatorio"].map((tab) => (
            <button
              key={tab}
              onClick={() => setSubTab(tab)}
              style={{
                padding: "8px 16px",
                background: subTab === tab ? "var(--atlas-blue)" : "var(--atlas-surface)",
                border: "1px solid var(--atlas-border)",
                color: subTab === tab ? "#fff" : "var(--atlas-text-secondary)",
                fontFamily: "monospace",
                fontSize: 11,
                borderRadius: 2,
                cursor: "pointer",
                textTransform: "uppercase"
              }}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Conteúdo das Tabs */}
      <div>
{subTab === "orbit" && <OrbitTab ticker={activeTicker} data={data} />}
    {subTab === "reflect" && <ReflectTab ticker={activeTicker} data={data} />}
    {subTab === "ciclos" && <CiclosTab ticker={activeTicker} data={data} />}
    {subTab === "analytics" && <AnalyticsTab ticker={activeTicker} data={data} analytics={analytics} />}
    {subTab === "relatorio" && <RelatorioTab ticker={activeTicker} data={data} />}
      </div>
    </div>
  );
}