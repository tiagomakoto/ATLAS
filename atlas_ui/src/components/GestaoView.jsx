// atlas_ui/src/components/GestaoView.jsx

import React, { useState, useEffect } from "react";
import TuneApprovalCard from "./GestaoView/TuneApprovalCard";
import OnboardingDrawer from "./GestaoView/OnboardingDrawer";

const API_BASE = "http://localhost:8000";

export default function GestaoView() {
  const [ativos, setAtivos] = useState([]);
  const [carregando, setCarregando] = useState(false);
  const [novoAtivo, setNovoAtivo] = useState("");
  const [onboardingMsg, setOnboardingMsg] = useState("");
  const [drawerOnboarding, setDrawerOnboarding] = useState(null);

  useEffect(() => {
    fetchAtivos();
  }, []);

  async function fetchAtivos() {
    try {
      const res = await fetch(`${API_BASE}/ativos`);
      const data = await res.json();
      setAtivos(data.ativos || []);
    } catch (e) {
      console.error("Erro ao carregar ativos:", e);
    }
  }

  async function handleOnboarding() {
    if (!novoAtivo.trim()) return;
    
    const ticker = novoAtivo.trim().toUpperCase();
    
    // 1. ABRIR DRAWER IMEDIATAMENTE (não aguardar resposta HTTP)
    setDrawerOnboarding(ticker);
    
    // 2. Chamar endpoint (não bloquear UI)
    setCarregando(true);
    setOnboardingMsg("");
    try {
      const res = await fetch(`${API_BASE}/delta-chaos/onboarding/iniciar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: ticker,
          confirm: true,
          description: `Onboarding ${ticker}`
        })
      });
      
      if (!res.ok) {
        // Se erro HTTP, fechar drawer e mostrar mensagem
        setDrawerOnboarding(null);
        const data = await res.json();
        setOnboardingMsg(`✗ ${data.detail || "Erro desconhecido"}`);
      } else {
        // Sucesso - manter drawer aberto
        setOnboardingMsg(`✓ ${ticker} — onboarding iniciado`);
        setTimeout(() => {
          setNovoAtivo("");
          fetchAtivos();
        }, 2000);
      }
    } catch (e) {
      // Se erro de rede, fechar drawer
      setDrawerOnboarding(null);
      setOnboardingMsg(`✗ Erro: ${e.message}`);
    } finally {
      setCarregando(false);
    }
  }

  async function handleExecutarTune(ticker) {
    setCarregando(true);
    try {
      const res = await fetch(`${API_BASE}/delta-chaos/tune`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: ticker,
          confirm: true,
          description: `Executar TUNE para ${ticker}`
        })
      });
      const data = await res.json();
      if (res.ok) {
        alert(`TUNE executado para ${ticker}\nRelatório: ${data.relatorio?.arquivo || "gerado"}`);
      } else {
        alert(`Erro: ${data.detail || "Erro desconhecido"}`);
      }
    } catch (e) {
      alert(`Erro: ${e.message}`);
    } finally {
      setCarregando(false);
    }
  }

  async function handleAplicarTune(ticker, tp, stop) {
    try {
      const res = await fetch(`${API_BASE}/delta-chaos/tune/aplicar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: ticker,
          tp: tp,
          stop: stop
        })
      });
      const data = await res.json();
      if (res.ok) {
        alert(`Parâmetros aplicados para ${ticker}:\nTP: ${tp*100}%\nSTOP: ${stop*100}%`);
        fetchAtivos();
      } else {
        alert(`Erro: ${data.detail || "Erro desconhecido"}`);
      }
    } catch (e) {
      alert(`Erro: ${e.message}`);
    }
  }

  async function handleSnapshot() {
    if (!confirm("Exportar estado atual do sistema para sessão com board?")) return;
    try {
      const res = await fetch(`${API_BASE}/report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ state: {}, analytics: {}, staleness: 0 })
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `snapshot_${new Date().toISOString().slice(0,10)}.md`;
        a.click();
        URL.revokeObjectURL(url);
        alert("Snapshot exportado com sucesso!");
      } else {
        alert("Erro ao exportar snapshot");
      }
    } catch (e) {
      alert(`Erro: ${e.message}`);
    }
  }

  async function handleBackup() {
    if (!confirm("Exportar dados operacionais para segurança? Isso pode levar alguns minutos.")) return;
    try {
      // Placeholder para lógica de backup
      alert("Funcionalidade de backup em desenvolvimento");
    } catch (e) {
      alert(`Erro: ${e.message}`);
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

  const badgeStyle = (status) => {
    const cores = {
      "vermelho": "rgba(239,68,68,0.2)",
      "amarelo": "rgba(245,158,11,0.2)",
      "verde": "rgba(34,197,94,0.2)",
      "cinza": "rgba(156,163,175,0.2)"
    };
    const coresBorda = {
      "vermelho": "var(--atlas-red)",
      "amarelo": "var(--atlas-amber)",
      "verde": "var(--atlas-green)",
      "cinza": "var(--atlas-gray)"
    };
    return {
      padding: "2px 8px",
      borderRadius: 4,
      fontSize: 9,
      fontFamily: "monospace",
      background: cores[status] || cores.cinza,
      border: `1px solid ${coresBorda[status] || coresBorda.cinza}`,
      color: status === "verde" ? "var(--atlas-green)" : status === "vermelho" ? "var(--atlas-red)" : status === "amarelo" ? "var(--atlas-amber)" : "var(--atlas-text-secondary)",
      display: "inline-block",
      marginRight: 8
    };
  };

  // Determinar status do ativo
  const getStatusAtivo = (ticker) => {
    const ativo = ativos.find(a => a.ticker === ticker);
    if (!ativo) return { cor: "cinza", label: "N/A" };

    // Lógica simplificada para demonstração
    // Na implementação real, usar historico_config para determinar estado
    if (ativo.status === "BLOQUEADO") return { cor: "vermelho", label: "Bloqueado" };
    if (ativo.status === "OPERAR") return { cor: "verde", label: "OPERAR" };
    if (ativo.status === "MONITORAR") return { cor: "amarelo", label: "Monitorar" };
    return { cor: "cinza", label: "N/A" };
  };

  return (
    <div style={{
      display: "flex", flexDirection: "column", gap: 16,
      maxWidth: 800,
      padding: 20
    }}>

    {/* Seção Por Ativo */}
    <div style={sectionStyle}>
      <span style={labelStyle}>Seção Por Ativo</span>

      {/* Onboarding */}
      <div style={{ marginBottom: 16, padding: 12, background: "rgba(59,130,246,0.08)", borderRadius: 2 }}>
        <span style={{...labelStyle, marginBottom: 4}}>Onboarding de novo ativo</span>
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
            disabled={!novoAtivo.trim() || carregando}
            style={{
              padding: "6px 14px",
              background: (!novoAtivo.trim() || carregando)
                ? "var(--atlas-border)"
                : "var(--atlas-blue)",
              border: "none", color: "#fff",
              fontFamily: "monospace", fontSize: 10,
              borderRadius: 2, cursor: "pointer",
              textTransform: "uppercase"
            }}
          >
            {carregando ? "..." : "Iniciar"}
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
      </div>

      {/* Lista de ativos com status */}
      <div>
        <span style={{...labelStyle, marginBottom: 4}}>Ativos</span>
        {ativos.length === 0 ? (
          <div style={{fontFamily: "monospace", fontSize: 10, color: "var(--atlas-text-secondary)"}}>
            Nenhum ativo carregado
          </div>
        ) : (
          <div style={{display: "flex", flexDirection: "column", gap: 8}}>
            {ativos.slice(0, 10).map(ativo => {
              const status = getStatusAtivo(ativo.ticker);
              return (
                <div key={ativo.ticker} style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: 8, background: "var(--atlas-bg)",
                  border: "1px solid var(--atlas-border)", borderRadius: 2
                }}>
                  <div style={{display: "flex", alignItems: "center", gap: 8}}>
                    <span style={badgeStyle(status.cor)}>{status.label}</span>
                    <span style={{fontFamily: "monospace", fontSize: 11}}>{ativo.ticker}</span>
                  </div>
                  <button
                    onClick={() => handleExecutarTune(ativo.ticker)}
                    disabled={carregando}
                    style={{
                      padding: "4px 10px",
                      background: "var(--atlas-surface)",
                      border: "1px solid var(--atlas-border)",
                      color: "var(--atlas-text-secondary)",
                      fontFamily: "monospace", fontSize: 9,
                      borderRadius: 2, cursor: "pointer",
                      textTransform: "uppercase"
                    }}
                  >
                    TUNE
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>

    {/* Seção Sistema */}
    <div style={sectionStyle}>
      <span style={labelStyle}>Seção Sistema</span>

      {/* Relatórios */}
      <div style={{ marginBottom: 12 }}>
        <span style={{...labelStyle, marginBottom: 4}}>Relatórios</span>
        <div style={{fontFamily: "monospace", fontSize: 10, color: "var(--atlas-text-secondary)"}}>
          Ver todos os relatórios gerados em relatorios/
        </div>
      </div>

      {/* Snapshot */}
      <div style={{ marginBottom: 12 }}>
        <span style={{...labelStyle, marginBottom: 4}}>Snapshot</span>
        <button
          onClick={handleSnapshot}
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
          Exportar estado atual
        </button>
      </div>

      {/* Backup */}
      <div>
        <span style={{...labelStyle, marginBottom: 4}}>Backup</span>
        <button
          onClick={handleBackup}
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
          Exportar dados operacionais
        </button>
      </div>
    </div>

    {/* Cartões de aprovação TUNE */}
    {ativos.some(a => a.tune_pendente) && (
      <div style={{display: "flex", flexDirection: "column", gap: 8}}>
        <span style={labelStyle}>Aprovação TUNE Pendente</span>
        {ativos.filter(a => a.tune_pendente).map(ativo => (
          <TuneApprovalCard
            key={ativo.ticker}
            ticker={ativo.ticker}
            onAplicar={handleAplicarTune}
          />
        ))}
      </div>
    )}

    {/* Drawer de Onboarding */}
    {drawerOnboarding && (
      <OnboardingDrawer 
        ticker={drawerOnboarding} 
        onClose={() => setDrawerOnboarding(null)} 
      />
    )}

    </div>
  );
}
