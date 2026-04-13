import React, { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";

const RelatorioTab = ({ ticker, data }) => {
  const [relatorioData, setRelatorioData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRelatorio = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/ativos/${ticker}/relatorio-tune`);
        if (!res.ok) {
          if (res.status === 404) {
            setRelatorioData(null); // Sem TUNE
            return;
          }
          throw new Error(`HTTP ${res.status}`);
        }
        const json = await res.json();
        setRelatorioData(json);
      } catch (err) {
        console.error("Erro ao carregar relatório TUNE:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (ticker) {
      fetchRelatorio();
    }
  }, [ticker]);

  const exportarMarkdown = () => {
    if (!relatorioData || !relatorioData.markdown) return;

    const filename = `TUNE_${ticker}_${relatorioData.ciclo}_${relatorioData.data}.md`;
    const blob = new Blob([relatorioData.markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div style={{ padding: 20, color: "var(--atlas-text-secondary)", textAlign: "center" }}>
        Carregando relatório...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 20, color: "var(--atlas-red)", textAlign: "center" }}>
        Erro: {error}
      </div>
    );
  }

  if (!relatorioData) {
    return (
      <div style={{ padding: 20, color: "var(--atlas-text-secondary)", textAlign: "center" }}>
        Nenhum TUNE executado para este ativo.
      </div>
    );
  }

  const {
    ticker: t,
    ciclo,
    data: dataExecucao,
    tp_atual,
    stop_atual,
    tp_novo,
    stop_novo,
    delta_tp,
    delta_stop,
    ir_valido,
    n_trades,
    confianca,
    janela_anos,
    ano_teste_ini,
    trials_rodados,
    trials_total,
    early_stop,
    retomado,
    reflect_mask,
    total_ciclos,
    reflect_mask_pct,
    ciclos_reais,
    ciclos_fallback,
    n_tp,
    n_stop,
    n_venc,
    acerto_pct,
    pior_data,
    pior_motivo,
    pior_pnl,
    diagnostico_executivo,
    historico_tunes
  } = relatorioData;

  return (
    <div style={{ fontFamily: "monospace", fontSize: 11, display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Cabeçalho */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "var(--atlas-bg)", border: "1px solid var(--atlas-border)", borderRadius: 4 }}>
        <h2 style={{ margin: 0, color: "var(--atlas-text-primary)" }}>Relatório de TUNE — {t} — {ciclo}</h2>
        <button
          onClick={exportarMarkdown}
          style={{
            padding: "6px 12px",
            background: "var(--atlas-blue)",
            color: "#fff",
            border: "none",
            borderRadius: 2,
            fontSize: 10,
            fontWeight: "bold",
            cursor: "pointer",
            fontFamily: "monospace"
          }}
        >
          Exportar .md
        </button>
      </div>

      {/* Aviso sobre proxies intradiários */}
      <div style={{
        padding: "12px 16px",
        background: "rgba(245, 158, 11, 0.1)",
        border: "1px solid var(--atlas-amber)",
        borderRadius: 4,
        fontSize: 10,
        color: "var(--atlas-amber)"
      }}>
        Os valores foram otimizados usando proxies intradiários: mínimo do dia como proxy de TP e máximo do dia como proxy de STOP. Em dias de alta volatilidade, esses proxies podem superestimar ganhos de TP e subestimar custos de STOP.
      </div>

      {/* Diagnóstico executivo */}
      <div style={{ padding: "16px 12px", background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", borderRadius: 4 }}>
        <h3 style={{ margin: "0 0 12px 0", color: "var(--atlas-text-primary)" }}>Diagnóstico executivo</h3>
        <p style={{ margin: 0, lineHeight: 1.5 }}>{diagnostico_executivo}</p>
      </div>

      {/* Parâmetros TUNE */}
      <div style={{ padding: "16px 12px", background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", borderRadius: 4 }}>
        <h3 style={{ margin: "0 0 12px 0", color: "var(--atlas-text-primary)" }}>Parâmetros TUNE</h3>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 10 }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--atlas-border)" }}>
              <th style={{ padding: "8px 4px", textAlign: "left" }}>Campo</th>
              <th style={{ padding: "8px 4px", textAlign: "center" }}>Atual</th>
              <th style={{ padding: "8px 4px", textAlign: "center" }}>Sugerido</th>
              <th style={{ padding: "8px 4px", textAlign: "center" }}>Delta</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ padding: "8px 4px", fontWeight: "bold" }}>Take Profit</td>
              <td style={{ padding: "8px 4px", textAlign: "center" }}>{tp_atual}</td>
              <td style={{ padding: "8px 4px", textAlign: "center" }}>{tp_novo}</td>
              <td style={{ padding: "8px 4px", textAlign: "center", color: delta_tp > 0 ? "var(--atlas-green)" : delta_tp < 0 ? "var(--atlas-red)" : "var(--atlas-text-secondary)" }}>
                {delta_tp > 0 ? "+" : ""}{delta_tp.toFixed(2)}
              </td>
            </tr>
            <tr>
              <td style={{ padding: "8px 4px", fontWeight: "bold" }}>Stop Loss</td>
              <td style={{ padding: "8px 4px", textAlign: "center" }}>{stop_atual}</td>
              <td style={{ padding: "8px 4px", textAlign: "center" }}>{stop_novo}</td>
              <td style={{ padding: "8px 4px", textAlign: "center", color: delta_stop > 0 ? "var(--atlas-green)" : delta_stop < 0 ? "var(--atlas-red)" : "var(--atlas-text-secondary)" }}>
                {delta_stop > 0 ? "+" : ""}{delta_stop.toFixed(2)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Qualidade da otimização */}
      <div style={{ padding: "16px 12px", background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", borderRadius: 4 }}>
        <h3 style={{ margin: "0 0 12px 0", color: "var(--atlas-text-primary)" }}>Qualidade da otimização</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 8, fontSize: 10 }}>
          <div><strong>IR válido (janela de teste):</strong> {ir_valido}</div>
          <div><strong>N trades na janela:</strong> {n_trades}</div>
          <div><strong>Confiança:</strong> {confianca}</div>
          <div><strong>Janela de teste:</strong> {janela_anos} anos ({ano_teste_ini}–{new Date().getFullYear()})</div>
          <div><strong>Trials rodados:</strong> {trials_rodados} / {trials_total}</div>
          <div><strong>Early stop ativado:</strong> {early_stop ? "SIM" : "NÃO"}</div>
          <div><strong>Study Optuna retomado:</strong> {retomado ? "SIM" : "NÃO"}</div>
        </div>
      </div>

      {/* Máscara REFLECT */}
      <div style={{ padding: "16px 12px", background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", borderRadius: 4 }}>
        <h3 style={{ margin: "0 0 12px 0", color: "var(--atlas-text-primary)" }}>Máscara REFLECT</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 8, fontSize: 10 }}>
          <div><strong>Ciclos mascarados (Edge C/D/E):</strong> {reflect_mask} de {total_ciclos} ({reflect_mask_pct.toFixed(1)}%)</div>
          <div><strong>Ciclos com REFLECT real:</strong> {ciclos_reais}</div>
          <div><strong>Ciclos com fallback B:</strong> {ciclos_fallback}</div>
        </div>
      </div>

      {/* Distribuição de saídas */}
      <div style={{ padding: "16px 12px", background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", borderRadius: 4 }}>
        <h3 style={{ margin: "0 0 12px 0", color: "var(--atlas-text-primary)" }}>Distribuição de saídas (janela de teste)</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 8, fontSize: 10 }}>
          <div><strong>Take Profit:</strong> {n_tp} ({acerto_pct.toFixed(1)}%)</div>
          <div><strong>Stop Loss:</strong> {n_stop} ({acerto_pct.toFixed(1)}%)</div>
          <div><strong>Vencimento:</strong> {n_venc} ({acerto_pct.toFixed(1)}%)</div>
          <div><strong>Acerto:</strong> {acerto_pct.toFixed(1)}%</div>
        </div>
      </div>

      {/* Pior trade */}
      <div style={{ padding: "16px 12px", background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", borderRadius: 4 }}>
        <h3 style={{ margin: "0 0 12px 0", color: "var(--atlas-text-primary)" }}>Pior trade (janela de teste)</h3>
        <div style={{ fontSize: 10 }}>
          <div><strong>Data:</strong> {pior_data}</div>
          <div><strong>Motivo:</strong> {pior_motivo}</div>
          <div><strong>P&L:</strong> R${pior_pnl.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        </div>
      </div>

      {/* Histórico de TUNEs aplicados */}
      <div style={{ padding: "16px 12px", background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", borderRadius: 4 }}>
        <h3 style={{ margin: "0 0 12px 0", color: "var(--atlas-text-primary)" }}>Histórico de TUNEs aplicados</h3>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 10 }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--atlas-border)" }}>
              <th style={{ padding: "8px 4px", textAlign: "left" }}>Data</th>
              <th style={{ padding: "8px 4px", textAlign: "center" }}>TP</th>
              <th style={{ padding: "8px 4px", textAlign: "center" }}>STOP</th>
              <th style={{ padding: "8px 4px", textAlign: "center" }}>IR válido</th>
              <th style={{ padding: "8px 4px", textAlign: "center" }}>Confiança</th>
            </tr>
          </thead>
          <tbody>
            {historico_tunes.map((tune, i) => (
              <tr key={i} style={{ borderBottom: "1px solid var(--atlas-border)" }}>
                <td style={{ padding: "8px 4px" }}>{tune.data}</td>
                <td style={{ padding: "8px 4px", textAlign: "center" }}>{tune.tp}</td>
                <td style={{ padding: "8px 4px", textAlign: "center" }}>{tune.stop}</td>
                <td style={{ padding: "8px 4px", textAlign: "center" }}>{tune.ir}</td>
                <td style={{ padding: "8px 4px", textAlign: "center" }}>{tune.confianca}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RelatorioTab;