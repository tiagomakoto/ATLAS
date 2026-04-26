// TUNE v3.0 — Painel de ranqueamento competitivo de estratégia por regime
// Sempre expandido (sem toggle). Confirmação por regime obrigatória antes do step 3.

import React, { useState } from "react";

const API_BASE = "http://localhost:8000";

const ELEICAO_COLORS = {
  competitiva:      "var(--atlas-blue)",
  estrutural_fixo:  "var(--atlas-amber)",
  bloqueado:        "var(--atlas-text-secondary)",
  in_progress:      "var(--atlas-text-secondary)",
};

const ELEICAO_LABELS = {
  competitiva:     "COMPETITIVA",
  estrutural_fixo: "ESTRUTURAL",
  bloqueado:       "BLOQUEADO",
  in_progress:     "AGUARDANDO",
};

function EleicaoTag({ status }) {
  const color = ELEICAO_COLORS[status] || "var(--atlas-text-secondary)";
  const label = ELEICAO_LABELS[status] || status?.toUpperCase() || "—";
  const isPulse = status === "in_progress";
  return (
    <span style={{
      fontFamily: "monospace",
      fontSize: 8,
      color,
      background: `${color}22`,
      padding: "1px 4px",
      borderRadius: 2,
      animation: isPulse ? "pulse 1.2s infinite" : "none",
    }}>
      {label}
    </span>
  );
}

function RegimeRow({ regime, dados, runId, ticker, onConfirmado, onRunIdMismatch }) {
  const [confirming, setConfirming] = useState(false);
  const [erro, setErro] = useState(null);

  const eleicao = dados.eleicao_status;
  const confirmado = dados.confirmado;
  const ranking = dados.ranking || [];
  const confirmavel = dados.confirmavel ?? (
    ["competitiva", "estrutural_fixo"].includes(eleicao)
    && (Boolean(dados.estrategia_eleita) || ranking.length > 0)
  );
  const motivoBloqueio = dados.motivo_bloqueio_confirmacao
    || (eleicao === "bloqueado" ? "Sem estratégia associada" : eleicao === "in_progress" ? "Eleição em andamento" : "Confirmação indisponível");
  const podeConfirmar = !confirmado && confirmavel;

  async function handleConfirmar() {
    setConfirming(true);
    setErro(null);
    try {
      const res = await fetch(`${API_BASE}/delta-chaos/tune/confirmar-regime`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker, regime, run_id: runId }),
      });
      const body = await res.json();
      if (!res.ok) {
        // run_id desatualizado: disparar re-fetch no pai para sincronizar
        if (res.status === 409 && body?.detail?.includes("run_id") && onRunIdMismatch) {
          onRunIdMismatch();
          setErro("Ranking desatualizado — recarregando...");
        } else {
          setErro(body?.detail || "Erro ao confirmar");
        }
      } else {
        onConfirmado(regime, body.estrategia);
      }
    } catch (e) {
      setErro("Erro de rede");
    } finally {
      setConfirming(false);
    }
  }

  return (
    <div style={{
      marginBottom: 10,
      padding: "8px 10px",
      background: confirmado ? "rgba(34,197,94,0.06)" : "var(--atlas-bg)",
      border: `1px solid ${confirmado ? "var(--atlas-green)" : "var(--atlas-border)"}`,
      borderRadius: 3,
    }}>
      {/* Header do regime */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontFamily: "monospace", fontSize: 10, color: "var(--atlas-text-primary)", fontWeight: "bold" }}>
            {regime}
          </span>
          <EleicaoTag status={eleicao} />
          {confirmado && (
            <span style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-green)" }}>✓ confirmado</span>
          )}
        </div>
        {!confirmado && (
          <button
            onClick={podeConfirmar ? handleConfirmar : undefined}
            disabled={confirming || !podeConfirmar}
            style={{
              padding: "3px 8px",
              background: podeConfirmar ? "var(--atlas-blue)" : "var(--atlas-border)",
              border: "none",
              color: "#fff",
              fontFamily: "monospace",
              fontSize: 8,
              borderRadius: 2,
              cursor: confirming ? "wait" : podeConfirmar ? "pointer" : "not-allowed",
              opacity: confirming ? 0.7 : podeConfirmar ? 1 : 0.65,
            }}
            title={podeConfirmar ? "" : motivoBloqueio}
          >
            {confirming ? "..." : `Confirmar ${regime}`}
          </button>
        )}
      </div>

      {erro && (
        <div style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-red)", marginBottom: 4 }}>{erro}</div>
      )}

      {/* Estratégia eleita (após confirmação) */}
      {confirmado && dados.estrategia_eleita && (
        <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-green)", marginBottom: 4 }}>
          Eleita: <strong>{dados.estrategia_eleita}</strong>
          {dados.n_trades != null && <span style={{ color: "var(--atlas-text-secondary)" }}> · N={dados.n_trades}</span>}
        </div>
      )}

      {/* Tabela de ranking (visível sempre que houver candidatos) */}
      {ranking.length > 0 && (
        <div style={{ marginTop: 4 }}>
          <div style={{
            display: "grid",
            gridTemplateColumns: "1.6fr .6fr .4fr .4fr .5fr",
            gap: 2,
            fontFamily: "monospace",
            fontSize: 8,
            color: "var(--atlas-text-secondary)",
            marginBottom: 2,
            paddingBottom: 2,
            borderBottom: "1px solid var(--atlas-border)",
          }}>
            <span>estratégia</span>
            <span>IR</span>
            <span>TP</span>
            <span>STOP</span>
            <span>N</span>
          </div>
          {ranking.map((item, idx) => (
            <div key={item.estrategia} style={{
              display: "grid",
              gridTemplateColumns: "1.6fr .6fr .4fr .4fr .5fr",
              gap: 2,
              fontFamily: "monospace",
              fontSize: 8,
              color: idx === 0 ? "var(--atlas-text-primary)" : "var(--atlas-text-secondary)",
              marginBottom: 1,
            }}>
              <span style={{ fontWeight: idx === 0 ? "bold" : "normal" }}>
                {idx === 0 ? "▶ " : "  "}{item.estrategia}
              </span>
              <span style={{ color: idx === 0 ? "var(--atlas-blue)" : "inherit" }}>
                {item.ir != null ? Number(item.ir).toFixed(3) : "—"}
              </span>
              <span>{item.tp != null ? Number(item.tp).toFixed(2) : "—"}</span>
              <span>{item.stop != null ? Number(item.stop).toFixed(2) : "—"}</span>
              <span>{item.n_trades ?? "—"}</span>
            </div>
          ))}
        </div>
      )}

      {!confirmado && !confirmavel && (
        <div style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-text-secondary)", marginTop: 2 }}>
          {motivoBloqueio}
        </div>
      )}
    </div>
  );
}

export default function TuneRankingPanel({ ticker, tuneRanking, onTodosConfirmados }) {
  const [bulkConfirming, setBulkConfirming] = useState(false);
  const [bulkErro, setBulkErro] = useState(null);
  const [localRanking, setLocalRanking] = useState(null);
  const [reloading, setReloading] = useState(false);

  const ranking = localRanking || tuneRanking;

  async function handleRunIdMismatch() {
    setReloading(true);
    try {
      const res = await fetch(`${API_BASE}/delta-chaos/calibracao/${ticker}`);
      if (!res.ok) return;
      const data = await res.json();
      const fresh = data?.step_2?.tune_ranking;
      if (fresh) setLocalRanking(fresh);
    } catch (_) {}
    finally { setReloading(false); }
  }
  if (!ranking) return null;

  const meta = ranking._meta || {};
  const runId = meta.run_id;
  const regimes = ranking.regimes || {};
  const concluido = ranking.concluido;
  const aguardando = ranking.aguardando_confirmacao_regimes;

  const elegiveisNaoConfirmados = Object.values(regimes).filter(
    (r) => !r.confirmado && (r.confirmavel ?? ["competitiva", "estrutural_fixo"].includes(r.eleicao_status))
  );

  function handleConfirmado(regime, estrategia) {
    setLocalRanking((prev) => {
      const base = prev || tuneRanking;
      const novosRegimes = {
        ...(base.regimes || {}),
        [regime]: {
          ...(base.regimes?.[regime] || {}),
          confirmado: true,
          estrategia_eleita: estrategia,
        },
      };
      const aindaAguardando = Object.values(novosRegimes).some(
        (r) => !r.confirmado && (r.confirmavel ?? ["competitiva", "estrutural_fixo"].includes(r.eleicao_status))
      );
      const updated = { ...base, regimes: novosRegimes, aguardando_confirmacao_regimes: aindaAguardando };
      if (!aindaAguardando && onTodosConfirmados) onTodosConfirmados();
      return updated;
    });
  }

  async function handleConfirmarTodos() {
    setBulkConfirming(true);
    setBulkErro(null);
    try {
      const res = await fetch(`${API_BASE}/delta-chaos/tune/confirmar-todos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker, run_id: runId }),
      });
      const body = await res.json();
      if (!res.ok) {
        setBulkErro(body?.detail || "Erro ao confirmar todos");
      } else {
        const confirmados = body.confirmados || [];
        setLocalRanking((prev) => {
          const base = prev || tuneRanking;
          const novosRegimes = { ...(base.regimes || {}) };
          for (const { regime, estrategia } of confirmados) {
            novosRegimes[regime] = { ...novosRegimes[regime], confirmado: true, estrategia_eleita: estrategia };
          }
          const updated = { ...base, regimes: novosRegimes, aguardando_confirmacao_regimes: false };
          return updated;
        });
        if (onTodosConfirmados) onTodosConfirmados();
      }
    } catch (e) {
      setBulkErro("Erro de rede");
    } finally {
      setBulkConfirming(false);
    }
  }

  return (
    <div style={{ marginTop: 12 }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "var(--atlas-text-primary)", fontWeight: "bold" }}>
          TUNE v3.0 — Eleição de Estratégia
          {meta.versao && (
            <span style={{ color: "var(--atlas-text-secondary)", fontWeight: "normal", marginLeft: 6 }}>
              v{meta.versao}
            </span>
          )}
        </div>
        {concluido && aguardando && elegiveisNaoConfirmados.length > 1 && (
          <button
            onClick={handleConfirmarTodos}
            disabled={bulkConfirming}
            style={{
              padding: "3px 8px",
              background: "var(--atlas-amber)",
              border: "none",
              color: "#000",
              fontFamily: "monospace",
              fontSize: 8,
              borderRadius: 2,
              cursor: bulkConfirming ? "wait" : "pointer",
              opacity: bulkConfirming ? 0.7 : 1,
            }}
            title="Auditoria recomendada antes do bulk approve"
          >
            {bulkConfirming ? "..." : `Confirmar todos (${elegiveisNaoConfirmados.length})`}
          </button>
        )}
      </div>

      {bulkErro && (
        <div style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-red)", marginBottom: 6 }}>{bulkErro}</div>
      )}

      {/* Status geral */}
      {!concluido && (
        <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)", marginBottom: 8 }}>
          Eleição em andamento...
        </div>
      )}

      {concluido && !aguardando && (
        <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-green)", marginBottom: 8 }}>
          ✓ Todos os regimes confirmados — step 3 liberado
        </div>
      )}

      {concluido && aguardando && (
        <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-amber)", marginBottom: 8 }}>
          ⚠ Confirme os regimes abaixo para liberar o step 3
        </div>
      )}

      {/* Regimes */}
      {reloading && (
        <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-blue)", marginBottom: 6 }}>
          Sincronizando ranking...
        </div>
      )}
      {Object.entries(regimes).map(([regime, dados]) => (
        <RegimeRow
          key={regime}
          regime={regime}
          dados={dados}
          runId={runId}
          ticker={ticker}
          onConfirmado={handleConfirmado}
          onRunIdMismatch={handleRunIdMismatch}
        />
      ))}
    </div>
  );
}

