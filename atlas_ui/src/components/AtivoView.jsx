import React, { useState, useEffect } from "react";
import WalkForwardChart from "../components/WalkForwardChart";
import DistributionChart from "../components/DistributionChart";
import ACFChart from "../components/ACFChart";
import TailMetrics from "../components/TailMetrics";

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

  const regimeConfidence = data?.historico?.slice(-1)[0]?.score || 0;
  const regimeAtual = data?.historico?.slice(-1)[0]?.regime || "DESCONHECIDO";
  const sizingAtual = data?.historico?.slice(-1)[0]?.sizing || 0;
  
  const historico = data?.historico || [];
  
  // 1. Ciclos Consecutivos no regime atual
  let ciclosConsecutivos = 0;
  for (let i = historico.length - 1; i >= 0; i--) {
    if (historico[i].regime === regimeAtual) ciclosConsecutivos++;
    else break;
  }
  
  // 2. Timeline Visual (últimos 12 ciclos) com sizing
  const timeline = historico.slice(-12).map((h) => ({
    regime: h.regime,
    ciclo: h.ciclo_id,
    data: h.timestamp?.slice(0, 10),
    sizing: h.sizing || 0,
    ir: h.ir || 0
  }));
  
  // 3. Transições Reais entre regimes
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
  
  // 4. Distribuição Histórica de Regimes
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
  
  // 5. Regime Mais Frequente
  const regimeMaisFrequente = distribuicaoPercentual[0]?.regime || "—";
  const countRegimeMaisFrequente = distribuicaoPercentual[0]?.count || 0;
  
  // 6. Cores Semânticas
  const getRegimeColor = (regime) => {
    if (!regime) return "var(--atlas-text-secondary)";
    const r = regime.toUpperCase();
    if (r.includes("ALTA") || r.includes("BULL")) return "var(--atlas-green)";
    if (r.includes("BAIXA") || r.includes("BEAR")) return "var(--atlas-red)";
    if (r.includes("TRANSICAO") || r.includes("TRANSIÇÃO")) return "var(--atlas-amber)";
    if (r.includes("NEUTRO")) return "var(--atlas-blue)";
    return "var(--atlas-text-secondary)";
  };
  
  const getRegimeBgColor = (regime) => {
    if (!regime) return "var(--atlas-surface)";
    const r = regime.toUpperCase();
    if (r.includes("ALTA") || r.includes("BULL")) return "rgba(34, 197, 94, 0.2)";
    if (r.includes("BAIXA") || r.includes("BEAR")) return "rgba(239, 68, 68, 0.2)";
    if (r.includes("TRANSICAO") || r.includes("TRANSIÇÃO")) return "rgba(245, 158, 11, 0.2)";
    if (r.includes("NEUTRO")) return "rgba(59, 130, 246, 0.2)";
    return "var(--atlas-surface)";
  };

  return (
    <div style={{ fontFamily: "monospace", fontSize: 11, display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Cards Principais */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Regime Atual</div>
          <div style={{ fontSize: 14, fontWeight: "bold", color: getRegimeColor(regimeAtual) }}>
            {regimeAtual}
            <span style={{ marginLeft: 8, fontSize: 10 }}>
              {sizingAtual === 1 ? "🟢 ON" : "⚪ OFF"}
            </span>
          </div>
        </div>
        
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Confiança</div>
          <div style={{ fontSize: 14, fontWeight: "bold", color: regimeConfidence > 0.7 ? "var(--atlas-green)" : "var(--atlas-amber)" }}>
            {(regimeConfidence * 100).toFixed(1)}%
          </div>
        </div>
        
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Ciclos Consecutivos</div>
          <div style={{ fontSize: 14, fontWeight: "bold" }}>{ciclosConsecutivos}</div>
        </div>
      </div>

      {/* Timeline Visual - Últimos 12 Ciclos */}
      <div>
        <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>
          Timeline de Regimes (Últimos 12 Ciclos)
        </h4>
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
              <div style={{ fontSize: 8, color: t.regime === regimeAtual ? "#fff" : "var(--atlas-text-secondary)" }}>
                {t.data}
              </div>
              <div style={{ fontSize: 9, fontWeight: "bold", color: t.regime === regimeAtual ? "#fff" : "var(--atlas-text-primary)", marginTop: 2 }}>
                {t.regime?.slice(0, 10)}
              </div>
              <div style={{ fontSize: 8, marginTop: 2, color: t.sizing === 1 ? "var(--atlas-green)" : "var(--atlas-text-secondary)" }}>
                {t.sizing === 1 ? "● ON" : "○ OFF"}
              </div>
              <div style={{ fontSize: 8, marginTop: 1, color: t.ir > 0 ? "var(--atlas-green)" : t.ir < 0 ? "var(--atlas-red)" : "var(--atlas-text-secondary)" }}>
                IR: {t.ir?.toFixed(2)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Distribuição Histórica e Regime Mais Frequente */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        <div>
          <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>
            Distribuição Histórica
          </h4>
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
                  <div style={{ 
                    width: 8, 
                    height: 8, 
                    borderRadius: "50%", 
                    background: getRegimeColor(d.regime) 
                  }} />
                  <span style={{ fontWeight: "bold", color: "var(--atlas-text-primary)" }}>
                    {d.regime}
                  </span>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ color: "var(--atlas-text-primary)", fontWeight: "bold" }}>
                    {d.count} ciclos
                  </div>
                  <div style={{ fontSize: 10, color: "var(--atlas-text-secondary)" }}>
                    {d.percentual}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>
            Regime Mais Frequente
          </h4>
          <div style={{ 
            padding: 16, 
            background: getRegimeBgColor(regimeMaisFrequente),
            border: `2px solid ${getRegimeColor(regimeMaisFrequente)}`,
            borderRadius: 6,
            textAlign: "center"
          }}>
            <div style={{ fontSize: 18, fontWeight: "bold", color: getRegimeColor(regimeMaisFrequente) }}>
              {regimeMaisFrequente}
            </div>
            <div style={{ fontSize: 12, color: "var(--atlas-text-secondary)", marginTop: 4 }}>
              {countRegimeMaisFrequente} ciclos ({distribuicaoPercentual[0]?.percentual}%)
            </div>
          </div>
          
          <div style={{ marginTop: 16 }}>
            <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>
              Total de Ciclos
            </h4>
            <div style={{ 
              padding: 12, 
              background: "var(--atlas-surface)",
              border: "1px solid var(--atlas-border)",
              borderRadius: 4,
              textAlign: "center",
              fontSize: 20,
              fontWeight: "bold"
            }}>
              {totalCiclos}
            </div>
          </div>
        </div>
      </div>

      {/* Transições Reais */}
      <div>
        <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>
          Transições Mais Frequentes
        </h4>
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
                  <span style={{ 
                    background: "var(--atlas-blue)", 
                    color: "#fff", 
                    padding: "2px 6px", 
                    borderRadius: 2,
                    fontSize: 9
                  }}>
                    {count}x
                  </span>
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{ 
            padding: 12, 
            color: "var(--atlas-text-secondary)",
            textAlign: "center",
            border: "1px dashed var(--atlas-border)",
            borderRadius: 4
          }}>
            Sem transições registradas
          </div>
        )}
      </div>
      
      {/* Legenda de Cores */}
      <div style={{ 
        padding: 8, 
        background: "var(--atlas-surface)", 
        border: "1px solid var(--atlas-border)",
        borderRadius: 4,
        fontSize: 9,
        display: "flex",
        gap: 16,
        flexWrap: "wrap"
      }}>
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
          <span>NEUTRO</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--atlas-amber)" }} />
          <span>TRANSIÇÃO</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <span style={{ color: "var(--atlas-green)" }}>● ON</span>
          <span style={{ color: "var(--atlas-text-secondary)" }}>|</span>
          <span style={{ color: "var(--atlas-text-secondary)" }}>○ OFF</span>
        </div>
      </div>
    </div>
  );
};

// === SUB-ABA: REFLECT ===
const ReflectTab = ({ ticker, data }) => {
  const historico = data?.historico || [];
  
  // 1. Matriz de Transição de Regimes
  const matrizTransicao = {};
  const contagemOrigem = {};
  
  for (let i = 1; i < historico.length; i++) {
    const origem = historico[i - 1].regime;
    const destino = historico[i].regime;
    
    if (!origem || !destino) continue;
    
    // Inicializar contagem de origem
    contagemOrigem[origem] = (contagemOrigem[origem] || 0) + 1;
    
    // Criar entrada na matriz
    if (!matrizTransicao[origem]) {
      matrizTransicao[origem] = {};
    }
    matrizTransicao[origem][destino] = (matrizTransicao[origem][destino] || 0) + 1;
  }
  
  // Calcular probabilidades de transição
  const probabilidadesTransicao = {};
  Object.entries(matrizTransicao).forEach(([origem, destinos]) => {
    const total = Object.values(destinos).reduce((sum, count) => sum + count, 0);
    probabilidadesTransicao[origem] = {};
    Object.entries(destinos).forEach(([destino, count]) => {
      probabilidadesTransicao[origem][destino] = {
        count,
        probability: (count / total * 100).toFixed(1)
      };
    });
  });
  
  // 2. Duração Média por Regime (quantos ciclos consecutivos)
  const duracoesPorRegime = {};
  let regimeAtual = null;
  let duracaoAtual = 0;
  
  historico.forEach((h) => {
    if (h.regime === regimeAtual) {
      duracaoAtual++;
    } else {
      if (regimeAtual) {
        if (!duracoesPorRegime[regimeAtual]) {
          duracoesPorRegime[regimeAtual] = [];
        }
        duracoesPorRegime[regimeAtual].push(duracaoAtual);
      }
      regimeAtual = h.regime;
      duracaoAtual = 1;
    }
  });
  
  // Adicionar última duração
  if (regimeAtual && duracaoAtual > 0) {
    if (!duracoesPorRegime[regimeAtual]) {
      duracoesPorRegime[regimeAtual] = [];
    }
    duracoesPorRegime[regimeAtual].push(duracaoAtual);
  }
  
  // Calcular estatísticas de duração
  const estatisticasDuracao = {};
  Object.entries(duracoesPorRegime).forEach(([regime, duracoes]) => {
    const media = duracoes.reduce((sum, d) => sum + d, 0) / duracoes.length;
    const max = Math.max(...duracoes);
    const min = Math.min(...duracoes);
    estatisticasDuracao[regime] = {
      media: media.toFixed(1),
      max,
      min,
      ocorrencias: duracoes.length
    };
  });
  
  // 3. Regimes únicos
  const regimesUnicos = [...new Set(historico.map(h => h.regime))].filter(Boolean);
  
  // 4. Transições Mais Frequentes (top 5)
  const todasTransicoes = [];
  Object.entries(matrizTransicao).forEach(([origem, destinos]) => {
    Object.entries(destinos).forEach(([destino, count]) => {
      todasTransicoes.push({ origem, destino, count });
    });
  });
  todasTransicoes.sort((a, b) => b.count - a.count);
  const topTransicoes = todasTransicoes.slice(0, 5);
  
  // 5. Probabilidade de Permanência no Regime Atual
  const ultimoRegime = historico.slice(-1)[0]?.regime;
  const probPermanencia = ultimoRegime && probabilidadesTransicao[ultimoRegime]?.[ultimoRegime]
    ? probabilidadesTransicao[ultimoRegime][ultimoRegime].probability
    : 0;
  
  // Cores Semânticas
  const getRegimeColor = (regime) => {
    if (!regime) return "var(--atlas-text-secondary)";
    const r = regime.toUpperCase();
    if (r.includes("ALTA") || r.includes("BULL")) return "var(--atlas-green)";
    if (r.includes("BAIXA") || r.includes("BEAR")) return "var(--atlas-red)";
    if (r.includes("TRANSICAO") || r.includes("TRANSIÇÃO")) return "var(--atlas-amber)";
    if (r.includes("NEUTRO")) return "var(--atlas-blue)";
    return "var(--atlas-text-secondary)";
  };
  
  const getRegimeBgColor = (regime) => {
    if (!regime) return "var(--atlas-surface)";
    const r = regime.toUpperCase();
    if (r.includes("ALTA") || r.includes("BULL")) return "rgba(34, 197, 94, 0.15)";
    if (r.includes("BAIXA") || r.includes("BEAR")) return "rgba(239, 68, 68, 0.15)";
    if (r.includes("TRANSICAO") || r.includes("TRANSIÇÃO")) return "rgba(245, 158, 11, 0.15)";
    if (r.includes("NEUTRO")) return "rgba(59, 130, 246, 0.15)";
    return "var(--atlas-surface)";
  };
  
  // Intensidade da cor baseada na probabilidade
  const getProbabilityColor = (prob) => {
    const p = parseFloat(prob);
    if (p >= 70) return "var(--atlas-green)";
    if (p >= 40) return "var(--atlas-amber)";
    return "var(--atlas-text-secondary)";
  };
  
  const getProbabilityIntensity = (prob) => {
    const p = parseFloat(prob) / 100;
    return Math.max(0.3, p);
  };

  return (
    <div style={{ fontFamily: "monospace", fontSize: 11, display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Cards de Status */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Regime Atual</div>
          <div style={{ fontSize: 14, fontWeight: "bold", color: getRegimeColor(ultimoRegime) }}>
            {ultimoRegime || "—"}
          </div>
        </div>
        
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Prob. Permanência</div>
          <div style={{ fontSize: 14, fontWeight: "bold", color: getProbabilityColor(probPermanencia) }}>
            {probPermanencia}%
          </div>
        </div>
        
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Total Transições</div>
          <div style={{ fontSize: 14, fontWeight: "bold" }}>
            {todasTransicoes.reduce((sum, t) => sum + t.count, 0)}
          </div>
        </div>
      </div>

      {/* Matriz de Transição */}
      <div>
        <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>
          Matriz de Transição de Regimes
        </h4>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 10 }}>
            <thead>
              <tr>
                <th style={{ 
                  padding: 8, 
                  textAlign: "left", 
                  background: "var(--atlas-surface)", 
                  border: "1px solid var(--atlas-border)",
                  color: "var(--atlas-text-primary)",
                  minWidth: 120
                }}>
                  Origem → Destino
                </th>
                {regimesUnicos.map(regime => (
                  <th 
                    key={regime} 
                    style={{ 
                      padding: 8, 
                      textAlign: "center", 
                      background: "var(--atlas-surface)",
                      border: "1px solid var(--atlas-border)",
                      color: getRegimeColor(regime),
                      fontWeight: "bold",
                      minWidth: 80
                    }}
                  >
                    {regime?.slice(0, 12)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {regimesUnicos.map(origem => (
                <tr key={origem}>
                  <td style={{ 
                    padding: 8, 
                    fontWeight: "bold", 
                    background: "var(--atlas-surface)",
                    border: "1px solid var(--atlas-border)",
                    color: getRegimeColor(origem),
                    minWidth: 120
                  }}>
                    {origem}
                  </td>
                  {regimesUnicos.map(destino => {
                    const transicao = probabilidadesTransicao[origem]?.[destino];
                    const count = transicao?.count || 0;
                    const prob = transicao?.probability || 0;
                    const isSame = origem === destino;
                    const hasData = count > 0;
                    
                    return (
                      <td 
                        key={destino} 
                        style={{ 
                          padding: 8, 
                          textAlign: "center", 
                          border: "1px solid var(--atlas-border)",
                          background: hasData ? "var(--atlas-surface)" : "var(--atlas-bg)",
                          color: hasData ? "var(--atlas-text-primary)" : "var(--atlas-text-secondary)",
                          opacity: hasData ? 1 : 0.4
                        }}
                      >
                        {hasData ? (
                          <div>
                            <div style={{ 
                              fontWeight: "bold", 
                              color: getProbabilityColor(prob),
                              fontSize: 11
                            }}>
                              {prob}%
                            </div>
                            <div style={{ fontSize: 9, color: "var(--atlas-text-secondary)" }}>
                              {count}x
                            </div>
                            {isSame && (
                              <div style={{ fontSize: 8, color: "var(--atlas-amber)", marginTop: 2 }}>
                                ↻
                              </div>
                            )}
                          </div>
                        ) : (
                          <span style={{ color: "var(--atlas-text-secondary)" }}>—</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top Transições */}
      <div>
        <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>
          Top 5 Transições Mais Frequentes
        </h4>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {topTransicoes.map((t, i) => {
            const totalTransicoes = todasTransicoes.reduce((sum, x) => sum + x.count, 0);
            const percentual = ((t.count / totalTransicoes) * 100).toFixed(1);
            
            return (
              <div 
                key={i}
                style={{
                  padding: "10px 12px",
                  background: getRegimeBgColor(t.destino),
                  border: `1px solid ${getRegimeColor(t.destino)}`,
                  borderRadius: 4,
                  display: "flex",
                  alignItems: "center",
                  gap: 12
                }}
              >
                <div style={{ 
                  width: 24, 
                  height: 24, 
                  borderRadius: "50%", 
                  background: "var(--atlas-blue)", 
                  color: "#fff",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 10,
                  fontWeight: "bold"
                }}>
                  #{i + 1}
                </div>
                
                <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1 }}>
                  <span style={{ color: getRegimeColor(t.origem), fontWeight: "bold" }}>
                    {t.origem}
                  </span>
                  <span style={{ color: "var(--atlas-text-secondary)", fontSize: 14 }}>→</span>
                  <span style={{ color: getRegimeColor(t.destino), fontWeight: "bold" }}>
                    {t.destino}
                  </span>
                </div>
                
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontWeight: "bold", color: "var(--atlas-text-primary)" }}>
                    {t.count}x
                  </div>
                  <div style={{ fontSize: 9, color: "var(--atlas-text-secondary)" }}>
                    {percentual}% do total
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Duração Média por Regime */}
      <div>
        <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>
          Duração Média por Regime (ciclos consecutivos)
        </h4>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
          {regimesUnicos.map(regime => {
            const stats = estatisticasDuracao[regime];
            if (!stats) return null;
            
            return (
              <div 
                key={regime}
                style={{
                  padding: 12,
                  background: getRegimeBgColor(regime),
                  border: `2px solid ${getRegimeColor(regime)}`,
                  borderRadius: 4
                }}
              >
                <div style={{ color: getRegimeColor(regime), fontWeight: "bold", marginBottom: 8 }}>
                  {regime}
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 8, fontSize: 10 }}>
                  <div>
                    <div style={{ color: "var(--atlas-text-secondary)" }}>Média</div>
                    <div style={{ fontWeight: "bold", fontSize: 14 }}>
                      {stats.media} ciclos
                    </div>
                  </div>
                  <div>
                    <div style={{ color: "var(--atlas-text-secondary)" }}>Máximo</div>
                    <div style={{ fontWeight: "bold", color: "var(--atlas-green)" }}>
                      {stats.max} ciclos
                    </div>
                  </div>
                  <div>
                    <div style={{ color: "var(--atlas-text-secondary)" }}>Mínimo</div>
                    <div style={{ fontWeight: "bold", color: "var(--atlas-red)" }}>
                      {stats.min} ciclos
                    </div>
                  </div>
                  <div>
                    <div style={{ color: "var(--atlas-text-secondary)" }}>Ocorrências</div>
                    <div style={{ fontWeight: "bold" }}>
                      {stats.ocorrencias}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Legenda */}
      <div style={{ 
        padding: 8, 
        background: "var(--atlas-surface)", 
        border: "1px solid var(--atlas-border)",
        borderRadius: 4,
        fontSize: 9,
        display: "flex",
        gap: 16,
        flexWrap: "wrap"
      }}>
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
          <span>NEUTRO</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--atlas-amber)" }} />
          <span>TRANSIÇÃO</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <span style={{ color: "var(--atlas-amber)" }}>↻</span>
          <span>Permanência no mesmo regime</span>
        </div>
      </div>
    </div>
  );
};


// === SUB-ABA: TRADES ===
const TradesTab = ({ ticker, data }) => {
  const [filtro, setFiltro] = useState("todos"); // todos | executados | rejeitados
  const [filtroRegime, setFiltroRegime] = useState("todos");
  
  const historico = data?.historico || [];
  
  // Separar ciclos executados (sizing=1) e rejeitados (sizing=0)
  const ciclosExecutados = historico.filter(h => h.sizing === 1);
  const ciclosRejeitados = historico.filter(h => h.sizing === 0);
  
  // Aplicar filtros
  let ciclosFiltrados = historico;
  if (filtro === "executados") ciclosFiltrados = ciclosExecutados;
  if (filtro === "rejeitados") ciclosFiltrados = ciclosRejeitados;
  
  if (filtroRegime !== "todos") {
    ciclosFiltrados = ciclosFiltrados.filter(h => h.regime === filtroRegime);
  }
  
  // Estatísticas
  const totalCiclos = historico.length;
  const totalExecutados = ciclosExecutados.length;
  const totalRejeitados = ciclosRejeitados.length;
  const taxaExecucao = totalCiclos > 0 ? ((totalExecutados / totalCiclos) * 100).toFixed(1) : 0;
  
  // IR Médio
  const irMedioExecutados = ciclosExecutados.length > 0 
    ? (ciclosExecutados.reduce((sum, h) => sum + (h.ir || 0), 0) / ciclosExecutados.length).toFixed(3)
    : 0;
  
  const irMedioRejeitados = ciclosRejeitados.length > 0 
    ? (ciclosRejeitados.reduce((sum, h) => sum + (h.ir || 0), 0) / ciclosRejeitados.length).toFixed(3)
    : 0;
  
  // Win Rate (ciclos com IR > 0)
  const winsExecutados = ciclosExecutados.filter(h => h.ir > 0).length;
  const winRate = ciclosExecutados.length > 0 
    ? ((winsExecutados / ciclosExecutados.length) * 100).toFixed(1)
    : 0;
  
  // Regimes únicos para filtro
  const regimesUnicos = [...new Set(historico.map(h => h.regime))].filter(Boolean);
  
  // Cores Semânticas
  const getRegimeColor = (regime) => {
    if (!regime) return "var(--atlas-text-secondary)";
    const r = regime.toUpperCase();
    if (r.includes("ALTA") || r.includes("BULL")) return "var(--atlas-green)";
    if (r.includes("BAIXA") || r.includes("BEAR")) return "var(--atlas-red)";
    if (r.includes("TRANSICAO") || r.includes("TRANSIÇÃO")) return "var(--atlas-amber)";
    if (r.includes("NEUTRO")) return "var(--atlas-blue)";
    return "var(--atlas-text-secondary)";
  };

  return (
    <div style={{ fontFamily: "monospace", fontSize: 11, display: "flex", flexDirection: "column", gap: 16 }}>
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
          <div style={{ fontSize: 18, fontWeight: "bold", color: "var(--atlas-red)" }}>
            {totalRejeitados}
          </div>
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
        <div style={{ color: "var(--atlas-text-secondary)", fontSize: 10 }}>Filtrar:</div>
        
        <select 
          value={filtro} 
          onChange={(e) => setFiltro(e.target.value)}
          style={{
            background: "var(--atlas-surface)",
            border: "1px solid var(--atlas-border)",
            color: "var(--atlas-text-primary)",
            fontFamily: "monospace",
            fontSize: 10,
            padding: "4px 8px"
          }}
        >
          <option value="todos">Todos os Ciclos</option>
          <option value="executados">Executados (ON)</option>
          <option value="rejeitados">Rejeitados (OFF)</option>
        </select>
        
        <select 
          value={filtroRegime} 
          onChange={(e) => setFiltroRegime(e.target.value)}
          style={{
            background: "var(--atlas-surface)",
            border: "1px solid var(--atlas-border)",
            color: "var(--atlas-text-primary)",
            fontFamily: "monospace",
            fontSize: 10,
            padding: "4px 8px"
          }}
        >
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

      {/* Tabela de Trades */}
      <div>
        <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>
          Histórico de Ciclos
        </h4>
        
        {ciclosFiltrados.length === 0 ? (
          <div style={{ 
            padding: 20, 
            textAlign: "center", 
            color: "var(--atlas-text-secondary)",
            border: "1px dashed var(--atlas-border)",
            borderRadius: 4
          }}>
            Nenhum ciclo encontrado com os filtros selecionados
          </div>
        ) : (
          <div style={{ 
            maxHeight: 400, 
            overflowY: "auto", 
            border: "1px solid var(--atlas-border)",
            borderRadius: 4
          }}>
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
                    <tr 
                      key={i} 
                      style={{ 
                        borderBottom: "1px solid var(--atlas-border)",
                        background: isExecutado ? "rgba(34, 197, 94, 0.05)" : "rgba(239, 68, 68, 0.05)",
                        opacity: isExecutado ? 1 : 0.7
                      }}
                    >
                      <td style={{ padding: 8, fontWeight: "bold" }}>
                        {ciclo.ciclo_id || "—"}
                      </td>
                      <td style={{ padding: 8, color: "var(--atlas-text-secondary)" }}>
                        {ciclo.data_ref?.slice(0, 10) || ciclo.timestamp?.slice(0, 10) || "—"}
                      </td>
                      <td style={{ padding: 8, color: getRegimeColor(ciclo.regime) }}>
                        {ciclo.regime || "—"}
                      </td>
                      <td style={{ padding: 8, textAlign: "center" }}>
                        <span style={{ 
                          padding: "2px 8px", 
                          borderRadius: 2, 
                          fontSize: 9,
                          background: isExecutado ? "var(--atlas-green)" : "var(--atlas-red)",
                          color: "#fff"
                        }}>
                          {isExecutado ? "ON" : "OFF"}
                        </span>
                      </td>
                      <td style={{ padding: 8, textAlign: "center" }}>
                        <div style={{ 
                          color: scorePct > 70 ? "var(--atlas-green)" : scorePct > 40 ? "var(--atlas-amber)" : "var(--atlas-red)"
                        }}>
                          {scorePct.toFixed(1)}%
                        </div>
                        <div style={{ fontSize: 8, color: "var(--atlas-text-secondary)" }}>
                          thresh: {(ciclo.thresh || 0).toFixed(3)}
                        </div>
                      </td>
                      <td style={{ padding: 8, textAlign: "center" }}>
                        <div style={{ 
                          color: irValue > 0 ? "var(--atlas-green)" : irValue < 0 ? "var(--atlas-red)" : "var(--atlas-text-secondary)",
                          fontWeight: "bold"
                        }}>
                          {irValue.toFixed(3)}
                        </div>
                      </td>
                      <td style={{ padding: 8, textAlign: "center", color: "var(--atlas-text-secondary)" }}>
                        {irTreino.toFixed(3)}
                      </td>
                      <td style={{ padding: 8, textAlign: "center", color: "var(--atlas-text-secondary)" }}>
                        {(ciclo.vol_21d || 0).toFixed(3)}
                      </td>
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
        <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>
          Performance por Regime
        </h4>
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
              <div 
                key={regime}
                style={{
                  padding: 12,
                  background: "var(--atlas-surface)",
                  border: `2px solid ${getRegimeColor(regime)}`,
                  borderRadius: 4
                }}
              >
                <div style={{ color: getRegimeColor(regime), fontWeight: "bold", marginBottom: 8 }}>
                  {regime}
                </div>
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
                    <div style={{ fontWeight: "bold", color: irMedioRegime > 0 ? "var(--atlas-green)" : "var(--atlas-red)" }}>
                      {irMedioRegime}
                    </div>
                  </div>
                  <div>
                    <div style={{ color: "var(--atlas-text-secondary)" }}>Win Rate</div>
                    <div style={{ fontWeight: "bold", color: winRateRegime > 50 ? "var(--atlas-green)" : "var(--atlas-amber)" }}>
                      {winRateRegime}%
                    </div>
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

// === SUB-ABA: ANALYTICS ===
const AnalyticsTab = ({ ticker, data, analytics }) => {
  const [threshold, setThreshold] = useState(analytics?.gateThreshold || 0.18);
  const [timeRange, setTimeRange] = useState("all");
  
  const historico = data?.historico || [];
  
  // Calcular estatísticas do IR
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
  
  // Simular impacto do threshold na seleção de trades
  const tradesComThreshold = historico.filter(h => (h.score || 0) >= threshold);
  const irComThreshold = tradesComThreshold.map(h => h.ir || 0).filter(v => v !== 0);
  const irMedioThreshold = irComThreshold.length > 0 
    ? (irComThreshold.reduce((a, b) => a + b, 0) / irComThreshold.length).toFixed(3)
    : 0;
  const winRateThreshold = irComThreshold.length > 0
    ? ((irComThreshold.filter(v => v > 0).length / irComThreshold.length) * 100).toFixed(1)
    : 0;
  
  // Distribuição por faixa de IR
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
  
  const maxCountFaixa = Math.max(...faixasIR.map(f => f.count), 1);
  
  // Cores Semânticas
  const getValueColor = (value, positive = true) => {
    const v = parseFloat(value);
    if (positive) {
      if (v > 0) return "var(--atlas-green)";
      if (v < 0) return "var(--atlas-red)";
      return "var(--atlas-text-secondary)";
    }
    return "var(--atlas-text-primary)";
  };

  return (
    <div style={{ fontFamily: "monospace", fontSize: 11, display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Controles */}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
        <div>
          <label style={{ color: "var(--atlas-text-secondary)", display: "block", marginBottom: 4 }}>
            Threshold do GATE
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
            style={{ width: 200 }}
          />
          <div style={{ fontSize: 10, color: "var(--atlas-text-primary)", marginTop: 2 }}>
            {threshold.toFixed(2)}
          </div>
        </div>
        
        <div>
          <label style={{ color: "var(--atlas-text-secondary)", display: "block", marginBottom: 4 }}>
            Período
          </label>
          <select 
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            style={{
              background: "var(--atlas-surface)",
              border: "1px solid var(--atlas-border)",
              color: "var(--atlas-text-primary)",
              fontFamily: "monospace",
              fontSize: 10,
              padding: "4px 8px"
            }}
          >
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

      {/* Cards de Estatísticas */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>P1% (Cauda Esquerda)</div>
          <div style={{ fontSize: 16, fontWeight: "bold", color: getValueColor(estatisticasIR.p1, false) }}>
            {estatisticasIR.p1}
          </div>
        </div>
        
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>P99% (Cauda Direita)</div>
          <div style={{ fontSize: 16, fontWeight: "bold", color: getValueColor(estatisticasIR.p99) }}>
            {estatisticasIR.p99}
          </div>
        </div>
        
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>IR Médio (com threshold)</div>
          <div style={{ fontSize: 16, fontWeight: "bold", color: getValueColor(irMedioThreshold) }}>
            {irMedioThreshold}
          </div>
        </div>
        
        <div style={{ padding: 12, background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)" }}>
          <div style={{ color: "var(--atlas-text-secondary)", marginBottom: 4 }}>Win Rate (com threshold)</div>
          <div style={{ fontSize: 16, fontWeight: "bold", color: winRateThreshold > 50 ? "var(--atlas-green)" : "var(--atlas-amber)" }}>
            {winRateThreshold}%
          </div>
        </div>
      </div>

      {/* Distribuição de IR */}
      <div>
        <h4 style={{ marginBottom: 12, color: "var(--atlas-text-primary)" }}>
          Distribuição de Information Ratio
        </h4>
        
        {/* Resumo rápido */}
        <div style={{ 
          display: "flex", 
          gap: 16, 
          marginBottom: 16,
          fontSize: 10
        }}>
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
        
        {/* Histograma */}
        <div style={{ 
          padding: 24,
          background: "var(--atlas-surface)",
          border: "1px solid var(--atlas-border)",
          borderRadius: 6
        }}>
          <div style={{ 
            display: "flex", 
            alignItems: "flex-end", 
            gap: 12, 
            height: 200,
            paddingBottom: 40  // espaço para labels
          }}>
            {faixasIR.map((faixa, i) => {
              const percentage = estatisticasIR.total > 0 
                ? ((faixa.count / estatisticasIR.total) * 100).toFixed(0) 
                : 0;
              const barHeight = percentage * 2; // escala para ficar visível
              
              return (
                <div 
                  key={i}
                  style={{
                    flex: 1,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "flex-end",
                    height: "100%",
                    position: "relative"
                  }}
                >
                  {/* Barra do histograma */}
                  <div 
                    style={{
                      width: "100%",
                      height: `${Math.max(barHeight, 8)}%`,  // altura mínima de 8%
                      background: faixa.color,
                      opacity: 0.85,
                      borderRadius: "4px 4px 0 0",
                      boxShadow: `0 -2px 8px ${faixa.color}40`,
                      transition: "all 0.3s ease",
                      position: "relative"
                    }}
                  >
                    {/* Valor dentro da barra (se houver espaço) */}
                    {barHeight > 15 && (
                      <div style={{
                        position: "absolute",
                        top: 8,
                        left: "50%",
                        transform: "translateX(-50%)",
                        fontSize: 11,
                        fontWeight: "bold",
                        color: "#fff",
                        textShadow: "0 1px 2px rgba(0,0,0,0.8)"
                      }}>
                        {faixa.count}
                      </div>
                    )}
                  </div>
                  
                  {/* Valor acima da barra */}
                  {barHeight <= 15 && (
                    <div style={{
                      fontSize: 11,
                      fontWeight: "bold",
                      color: faixa.color,
                      marginBottom: 4,
                      minHeight: 16
                    }}>
                      {faixa.count}
                    </div>
                  )}
                  
                  {/* Porcentagem */}
                  <div style={{
                    fontSize: 9,
                    color: "var(--atlas-text-secondary)",
                    marginTop: 2
                  }}>
                    {percentage}%
                  </div>
                  
                  {/* Label da faixa */}
                  <div style={{ 
                    position: "absolute",
                    bottom: -36,
                    left: "50%",
                    transform: "translateX(-50%)",
                    fontSize: 10,  // aumentado
                    fontWeight: "500",
                    color: faixa.color,
                    textAlign: "center",
                    whiteSpace: "nowrap"
                  }}>
                    {faixa.label}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        
        {/* Legenda */}
        <div style={{ 
          display: "flex", 
          justifyContent: "center", 
          gap: 20, 
          marginTop: 12,
          padding: 8,
          background: "var(--atlas-bg)",
          borderRadius: 4,
          fontSize: 10
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 12, height: 12, background: "var(--atlas-red)", borderRadius: 2, opacity: 0.85 }} />
            <span style={{ color: "var(--atlas-text-primary)" }}>Prejuízo (IR &lt; 0)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 12, height: 12, background: "var(--atlas-amber)", borderRadius: 2, opacity: 0.85 }} />
            <span style={{ color: "var(--atlas-text-primary)" }}>Neutro (IR ≈ 0)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 12, height: 12, background: "var(--atlas-green)", borderRadius: 2, opacity: 0.85 }} />
            <span style={{ color: "var(--atlas-text-primary)" }}>Lucro (IR &gt; 0)</span>
          </div>
        </div>
      </div>



      {/* Estatísticas Detalhadas */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        <div>
          <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>
            Métricas Estatísticas
          </h4>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 8 }}>
            {[
              { label: "Média", value: estatisticasIR.media },
              { label: "Mediana", value: estatisticasIR.mediana },
              { label: "Desvio Padrão", value: estatisticasIR.std },
              { label: "Mínimo", value: estatisticasIR.min },
              { label: "Máximo", value: estatisticasIR.max },
              { label: "Total Ciclos", value: estatisticasIR.total },
            ].map((stat, i) => (
              <div 
                key={i}
                style={{
                  padding: 8,
                  background: "var(--atlas-surface)",
                  border: "1px solid var(--atlas-border)",
                  borderRadius: 2
                }}
              >
                <div style={{ color: "var(--atlas-text-secondary)", fontSize: 9 }}>
                  {stat.label}
                </div>
                <div style={{ fontWeight: "bold", color: getValueColor(stat.value) }}>
                  {stat.value}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div>
          <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>
            Impacto do Threshold
          </h4>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ 
              padding: 12, 
              background: "var(--atlas-surface)", 
              border: "1px solid var(--atlas-border)",
              borderRadius: 4
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ color: "var(--atlas-text-secondary)" }}>Trades Selecionados</span>
                <span style={{ fontWeight: "bold" }}>
                  {tradesComThreshold.length} / {historico.length}
                </span>
              </div>
              <div style={{ 
                height: 6, 
                background: "var(--atlas-border)", 
                borderRadius: 3,
                overflow: "hidden"
              }}>
                <div style={{ 
                  width: `${(tradesComThreshold.length / Math.max(historico.length, 1)) * 100}%`,
                  height: "100%",
                  background: "var(--atlas-blue)",
                  borderRadius: 3
                }} />
              </div>
            </div>
            
            <div style={{ 
              padding: 12, 
              background: "var(--atlas-surface)", 
              border: "1px solid var(--atlas-border)",
              borderRadius: 4
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ color: "var(--atlas-text-secondary)" }}>IR Médio Filtrado</span>
                <span style={{ fontWeight: "bold", color: getValueColor(irMedioThreshold) }}>
                  {irMedioThreshold}
                </span>
              </div>
              <div style={{ fontSize: 9, color: "var(--atlas-text-secondary)" }}>
                vs. IR Geral: {estatisticasIR.media}
              </div>
            </div>
            
            <div style={{ 
              padding: 12, 
              background: "var(--atlas-surface)", 
              border: "1px solid var(--atlas-border)",
              borderRadius: 4
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ color: "var(--atlas-text-secondary)" }}>Win Rate Filtrado</span>
                <span style={{ fontWeight: "bold", color: winRateThreshold > 50 ? "var(--atlas-green)" : "var(--atlas-amber)" }}>
                  {winRateThreshold}%
                </span>
              </div>
              <div style={{ fontSize: 9, color: "var(--atlas-text-secondary)" }}>
                Trades com IR &gt; 0
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Gráficos */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        <div>
          <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>
            Walk-Forward Performance
          </h4>
          {analytics?.walkForward ? (
            <WalkForwardChart data={analytics.walkForward} />
          ) : (
            <div style={{ 
              padding: 40, 
              textAlign: "center", 
              color: "var(--atlas-text-secondary)",
              border: "1px dashed var(--atlas-border)",
              borderRadius: 4
            }}>
              Dados de walk-forward não disponíveis
            </div>
          )}
        </div>
        
        <div>
          <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>
            Distribuição de Retornos
          </h4>
          {analytics?.distribution ? (
            <DistributionChart data={analytics.distribution} />
          ) : (
            <div style={{ 
              padding: 40, 
              textAlign: "center", 
              color: "var(--atlas-text-secondary)",
              border: "1px dashed var(--atlas-border)",
              borderRadius: 4
            }}>
              Dados de distribuição não disponíveis
            </div>
          )}
        </div>
        
        <div>
          <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>
            Autocorrelação (ACF)
          </h4>
          {analytics?.acf ? (
            <ACFChart data={analytics.acf} />
          ) : (
            <div style={{ 
              padding: 40, 
              textAlign: "center", 
              color: "var(--atlas-text-secondary)",
              border: "1px dashed var(--atlas-border)",
              borderRadius: 4
            }}>
              Dados de ACF não disponíveis
            </div>
          )}
        </div>
        
        <div>
          <h4 style={{ marginBottom: 8, color: "var(--atlas-text-primary)" }}>
            Caudas Pesadas (Fat Tails)
          </h4>
          {analytics?.fatTails ? (
            <TailMetrics data={analytics.fatTails} />
          ) : (
            <div style={{ 
              padding: 40, 
              textAlign: "center", 
              color: "var(--atlas-text-secondary)",
              border: "1px dashed var(--atlas-border)",
              borderRadius: 4
            }}>
              Dados de fat tails não disponíveis
            </div>
          )}
        </div>
      </div>
      
      {/* Legenda */}
      <div style={{ 
        padding: 8, 
        background: "var(--atlas-surface)", 
        border: "1px solid var(--atlas-border)",
        borderRadius: 4,
        fontSize: 9,
        display: "flex",
        gap: 16,
        flexWrap: "wrap"
      }}>
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
export default function AtivoView({ activeTicker, analytics }) {
  const [subTab, setSubTab] = useState("orbit");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchAtivo() {
      if (!activeTicker) return;
      
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/ativos/${activeTicker}`);
        
        if (!res.ok) {
          throw new Error(`Erro HTTP: ${res.status}`);
        }
        
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

  if (loading) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "var(--atlas-text-secondary)" }}>
        <div style={{ fontSize: 16, marginBottom: 8 }}>Carregando dados do ativo...</div>
        <div style={{ fontSize: 12 }}>{activeTicker}</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "var(--atlas-red)" }}>
        <div style={{ fontSize: 16, marginBottom: 8 }}>Erro ao carregar dados</div>
        <div style={{ fontSize: 12 }}>{error}</div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Tabs */}
      <div style={{ display: "flex", gap: 8, borderBottom: "1px solid var(--atlas-border)", paddingBottom: 8 }}>
        {["orbit", "reflect", "trades", "analytics"].map((tab) => (
          <button
            key={tab}
            onClick={() => setSubTab(tab)}
            style={{
              padding: "6px 12px",
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

      {/* Conteúdo das Tabs */}
      {subTab === "orbit" && <OrbitTab ticker={activeTicker} data={data} />}
      
      {subTab === "reflect" && <ReflectTab ticker={activeTicker} data={data} />}  
      
      {subTab === "trades" && <TradesTab ticker={activeTicker} data={data} />}
     
      {subTab === "analytics" && <AnalyticsTab ticker={activeTicker} data={data} analytics={analytics} />}
    </div>
  );
}