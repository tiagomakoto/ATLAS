import React, { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";

const PULSE_STYLE = `
  @keyframes atlasRelPulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }
`;

function formatDate(iso) {
  if (!iso) return "—";
  try {
    const [y, m, d] = iso.split("-");
    if (y && m && d) return `${d}/${m}/${y}`;
  } catch (_) {}
  return iso;
}

function summarizeValor(valorNovo) {
  if (valorNovo === null || valorNovo === undefined) return "—";
  if (typeof valorNovo === "string") return valorNovo;
  if (typeof valorNovo === "object") {
    const keys = Object.keys(valorNovo);
    const n = keys.length;
    if (n <= 3) return `${n} regimes (${keys.join(", ")})`;
    return `${n} regimes`;
  }
  return String(valorNovo);
}

function renderValor(valor) {
  if (valor === null || valor === undefined) return <span style={{ color: "var(--atlas-text-secondary)" }}>—</span>;
  if (typeof valor === "string") return <span>{valor}</span>;
  if (typeof valor === "boolean") return <span>{valor ? "SIM" : "NÃO"}</span>;
  if (typeof valor === "object") {
    const keys = Object.keys(valor);
    return (
      <table style={{ borderCollapse: "collapse", fontSize: 10, marginTop: 2 }}>
        <tbody>
          {keys.map((k) => (
            <tr key={k} style={{ borderBottom: "1px solid var(--atlas-border)" }}>
              <td style={{ padding: "2px 8px 2px 0", color: "var(--atlas-text-secondary)", fontWeight: "bold" }}>{k}</td>
              <td style={{ padding: "2px 0" }}>{String(valor[k])}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }
  return <span>{String(valor)}</span>;
}

const DETAIL_FIELDS = [
  { key: "data", label: "Data", render: (v) => <span>{formatDate(v)}</span> },
  { key: "modulo", label: "Módulo" },
  { key: "parametro", label: "Parâmetro" },
  { key: "valor_anterior", label: "Valor anterior", renderFn: true },
  { key: "valor_novo", label: "Valor novo", renderFn: true },
  { key: "motivo", label: "Motivo" },
  { key: "bulk", label: "Bulk", render: (v) => v ? <span style={{ background: "var(--atlas-blue)", color: "#fff", padding: "1px 6px", borderRadius: 2, fontSize: 10 }}>BULK</span> : null },
];

const RelatorioTab = ({ ticker }) => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState({});
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (!ticker) return;
    setLoading(true);
    setError(null);
    setEntries([]);
    setExpanded({});

    fetch(`${API_BASE}/delta-chaos/ativos/${ticker}/historico-config`)
      .then((res) => {
        if (res.status === 404) return { historico_config: [] };
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json) => {
        const list = json.historico_config || [];
        setEntries(list);
        if (list.length > 0) setExpanded({ 0: true });
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [ticker]);

  const toggle = (i) => setExpanded((prev) => ({ ...prev, [i]: !prev[i] }));

  const exportarMarkdown = async () => {
    setExporting(true);
    try {
      const res = await fetch(`${API_BASE}/ativos/${ticker}/relatorio-tune`);
      if (!res.ok) {
        alert(
          res.status === 404
            ? "Relatório TUNE não disponível para este ciclo."
            : `Erro ${res.status} ao gerar relatório.`
        );
        return;
      }
      const json = await res.json();
      if (!json?.markdown) { alert("Relatório sem markdown."); return; }
      const filename = `TUNE_${ticker}_${json.ciclo}_${json.data}.md`;
      const blob = new Blob([json.markdown], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  const baseCard = {
    background: "var(--atlas-surface)",
    border: "1px solid var(--atlas-border)",
    borderRadius: 4,
    fontFamily: "monospace",
    fontSize: 11,
  };

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <style>{PULSE_STYLE}</style>
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              ...baseCard,
              height: 40,
              animation: "atlasRelPulse 1.5s infinite",
            }}
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "12px 16px", color: "var(--atlas-red)", background: "rgba(239,68,68,0.08)", border: "1px solid var(--atlas-red)", borderRadius: 4, fontFamily: "monospace", fontSize: 11 }}>
        Erro: {error}
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <style>{PULSE_STYLE}</style>

      {/* Header */}
      <div style={{ fontFamily: "monospace", fontSize: 12, fontWeight: "bold", color: "var(--atlas-text-primary)", paddingBottom: 4, borderBottom: "1px solid var(--atlas-border)" }}>
        Histórico de configuração — {ticker}
      </div>

      {entries.length === 0 ? (
        <div style={{ padding: 24, textAlign: "center", color: "var(--atlas-text-secondary)", fontFamily: "monospace", fontSize: 11, border: "1px dashed var(--atlas-border)", borderRadius: 4 }}>
          Nenhuma calibração registrada para este ativo.
        </div>
      ) : (
        entries.map((entry, i) => {
          const isOpen = !!expanded[i];
          return (
            <div key={i} style={baseCard}>
              {/* Linha colapsada */}
              <div
                onClick={() => toggle(i)}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "10px 14px",
                  cursor: "pointer",
                  userSelect: "none",
                  gap: 8,
                }}
              >
                <span style={{ color: "var(--atlas-text-primary)", fontWeight: "bold" }}>
                  {formatDate(entry.data)}
                  <span style={{ color: "var(--atlas-text-secondary)", fontWeight: "normal", marginLeft: 8 }}>·</span>
                  <span style={{ color: "var(--atlas-text-secondary)", fontWeight: "normal", marginLeft: 8 }}>{entry.parametro}</span>
                </span>
                <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ color: "var(--atlas-text-secondary)" }}>
                    {summarizeValor(entry.valor_novo)}
                  </span>
                  <span style={{ color: "var(--atlas-text-secondary)", transform: isOpen ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.15s", display: "inline-block" }}>▶</span>
                </span>
              </div>

              {/* Painel expandido */}
              {isOpen && (
                <div style={{ borderTop: "1px solid var(--atlas-border)", padding: "12px 14px", display: "flex", flexDirection: "column", gap: 8 }}>
                  <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 10 }}>
                    <tbody>
                      {DETAIL_FIELDS.map(({ key, label, render, renderFn }) => {
                        if (!(key in entry)) return null;
                        const val = entry[key];
                        if (key === "bulk" && !val) return null;
                        const rendered = render
                          ? render(val)
                          : renderFn
                          ? renderValor(val)
                          : <span>{val === null || val === undefined ? "—" : String(val)}</span>;
                        if (rendered === null) return null;
                        return (
                          <tr key={key} style={{ verticalAlign: "top" }}>
                            <td style={{ padding: "4px 12px 4px 0", color: "var(--atlas-text-secondary)", fontWeight: "bold", whiteSpace: "nowrap", width: 130 }}>{label}</td>
                            <td style={{ padding: "4px 0", color: "var(--atlas-text-primary)" }}>{rendered}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>

                  {i === 0 && (
                    <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 4 }}>
                      <button
                        onClick={exportarMarkdown}
                        disabled={exporting}
                        style={{
                          padding: "5px 12px",
                          background: exporting ? "var(--atlas-surface)" : "var(--atlas-blue)",
                          color: exporting ? "var(--atlas-text-secondary)" : "#fff",
                          border: "1px solid var(--atlas-border)",
                          borderRadius: 2,
                          fontSize: 10,
                          fontWeight: "bold",
                          cursor: exporting ? "not-allowed" : "pointer",
                          fontFamily: "monospace",
                        }}
                      >
                        {exporting ? "Gerando..." : "Exportar .md"}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })
      )}
    </div>
  );
};

export default RelatorioTab;
