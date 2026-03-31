// atlas_ui/src/components/Configuracao.jsx
import React, { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";

export default function Configuracao({ ticker }) {
  const [takeProfit, setTakeProfit] = useState("");
  const [stopLoss, setStopLoss] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [currentConfig, setCurrentConfig] = useState({
    take_profit: null,
    stop_loss: null
  });
  const [fetching, setFetching] = useState(true);

  // ✅ Carregar config atual do JSON do ativo
  useEffect(() => {
    if (!ticker) return;
    async function fetchConfig() {
      setFetching(true);
      try {
        const res = await fetch(`${API_BASE}/ativos/${ticker}`);
        if (!res.ok) throw new Error(`Erro HTTP: ${res.status}`);
        
        const data = await res.json();
        
        // ✅ EXTRAIR TP E STOP LOSS DO JSON (campos na raiz)
        const tpValue = data.take_profit ?? null;
        const slValue = data.stop_loss ?? null;
        
        setCurrentConfig({
          take_profit: tpValue,
          stop_loss: slValue
        });
        
        // ✅ PREENCHER INPUTS COM VALORES ATUAIS
        setTakeProfit(tpValue !== null ? String(tpValue) : "");
        setStopLoss(slValue !== null ? String(slValue) : "");
      } catch (err) {
        console.error("Erro ao carregar config:", err);
        setMessage({ type: "error", text: err.message });
      } finally {
        setFetching(false);
      }
    }

    fetchConfig();
  }, [ticker]);

  // ✅ Salvar alterações
  async function handleSave() {
    if (!takeProfit || !stopLoss) {
      setMessage({ type: "error", text: "Preencha todos os campos" });
      return;
    }
    setLoading(true);
    setMessage(null);

    try {
      const res = await fetch(`${API_BASE}/ativos/${ticker}/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          data: {
            take_profit: parseFloat(takeProfit),
            stop_loss: parseFloat(stopLoss)
          },
          description: "Atualização via Manutenção → Configuração",
          confirm: true
        })
      });
      
      if (res.ok) {
        setMessage({ type: "success", text: "Configuração salva com sucesso!" });
        
        // Recarregar config atualizada
        const resConfig = await fetch(`${API_BASE}/ativos/${ticker}`);
        const data = await resConfig.json();
        setCurrentConfig({
          take_profit: data.take_profit ?? null,
          stop_loss: data.stop_loss ?? null
        });
        setTakeProfit(String(data.take_profit ?? ""));
        setStopLoss(String(data.stop_loss ?? ""));
      } else {
        const error = await res.json();
        setMessage({ type: "error", text: error.detail?.message || "Erro ao salvar" });
      }
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setLoading(false);
    }
  }

  if (fetching) {
    return <div style={{ padding: 20, color: "var(--atlas-text-secondary)" }}>Carregando...</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Mensagem de feedback */}
        {message && (
        <div style={{
            padding: "8px 12px",
            background: message.type === "success" ? "rgba(34, 197, 94, 0.2)" : "rgba(239, 68, 68, 0.2)",
            border: `1px solid ${message.type === "success" ? "var(--atlas-green)" : "var(--atlas-red)"}`,
            borderRadius: 4,
            fontFamily: "monospace",
            fontSize: 10,
            color: message.type === "success" ? "var(--atlas-green)" : "var(--atlas-red)"
        }}>
            {message.text}
        </div>
        )}

        {/* TP e SL inputs — SEM container interno */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        {/* Take Profit */}
        <div>
            <label style={{
            fontFamily: "monospace",
            fontSize: 9,
            color: "var(--atlas-text-secondary)",
            textTransform: "uppercase",
            display: "block",
            marginBottom: 4
            }}>
            Take Profit
            </label>
            <input
            type="number"
            step="0.01"
            min="0.01"
            max="0.99"
            value={takeProfit}
            onChange={(e) => setTakeProfit(e.target.value)}
            style={{
                width: "100%",
                padding: "6px 8px",
                background: "var(--atlas-bg)",
                border: "1px solid var(--atlas-border)",
                color: "var(--atlas-text-primary)",
                fontFamily: "monospace",
                fontSize: 11,
                borderRadius: 2
            }}
            />
            <div style={{
            fontFamily: "monospace",
            fontSize: 9,
            color: "var(--atlas-text-secondary)",
            marginTop: 4
            }}>
            Proporção do prêmio (ex: 0.90 = 90%)
            </div>
            <div style={{
            fontFamily: "monospace",
            fontSize: 9,
            color: "var(--atlas-blue)",
            marginTop: 2,
            fontWeight: "bold"
            }}>
            Atual: {currentConfig.take_profit !== null ? currentConfig.take_profit : "—"}
            </div>
        </div>

        {/* Stop Loss */}
        <div>
            <label style={{
            fontFamily: "monospace",
            fontSize: 9,
            color: "var(--atlas-text-secondary)",
            textTransform: "uppercase",
            display: "block",
            marginBottom: 4
            }}>
            Stop Loss
            </label>
            <input
            type="number"
            step="0.1"
            min="0.1"
            value={stopLoss}
            onChange={(e) => setStopLoss(e.target.value)}
            style={{
                width: "100%",
                padding: "6px 8px",
                background: "var(--atlas-bg)",
                border: "1px solid var(--atlas-border)",
                color: "var(--atlas-text-primary)",
                fontFamily: "monospace",
                fontSize: 11,
                borderRadius: 2
            }}
            />
            <div style={{
            fontFamily: "monospace",
            fontSize: 9,
            color: "var(--atlas-text-secondary)",
            marginTop: 4
            }}>
            Múltiplo do prêmio (ex: 2.0 = 2×)
            </div>
            <div style={{
            fontFamily: "monospace",
            fontSize: 9,
            color: "var(--atlas-blue)",
            marginTop: 2,
            fontWeight: "bold"
            }}>
            Atual: {currentConfig.stop_loss !== null ? currentConfig.stop_loss : "—"}
            </div>
        </div>
        </div>

        {/* Botão Salvar */}
        <button
        onClick={handleSave}
        disabled={loading || !takeProfit || !stopLoss}
        style={{
            marginTop: 16,
            padding: "8px 16px",
            background: "var(--atlas-blue)",
            border: "none",
            color: "#fff",
            fontFamily: "monospace",
            fontSize: 10,
            borderRadius: 2,
            cursor: (loading || !takeProfit || !stopLoss) ? "not-allowed" : "pointer",
            textTransform: "uppercase",
            opacity: (loading || !takeProfit || !stopLoss) ? 0.6 : 1
        }}
        >
        {loading ? "Salvando..." : "Salvar Alterações"}
        </button>

        {/* Exportar — REMOVER ESTE BLOCO INTEIRO */}
        {/* <div style={{...}}>Exportação...</div> */}
    </div>
    );
}