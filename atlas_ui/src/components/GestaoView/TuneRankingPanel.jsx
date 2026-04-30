// TUNE v3.1 — Painel de resultados com aplicação automática e gate de anomalia CEO

import React, { useState } from "react";

const API_BASE = "http://localhost:8000";

function fmt(v, decimals = 2) {
  if (v == null) return "—";
  return Number(v).toFixed(decimals);
}

function formatDateTimeBR(value) {
  if (!value) return "";
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return "";
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(dt.getDate())}/${pad(dt.getMonth() + 1)}/${dt.getFullYear()} ${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
}

function RegimeRow({ regime, dados, runId, ticker, nMinimoCalib, onResolvido }) {
  const [actionState, setActionState] = useState({ loading: null, erro: null });

  const eleicao = dados.eleicao_status;
  const anomalia = dados.anomalia || {};
  const anomalyDetected = anomalia.detectada === true;
  const aplicacao = dados.aplicacao;
  const estrategia = dados.estrategia_eleita;
  const statusCalib = dados.status_calibracao;

  const isBlocked = eleicao === "bloqueado";
  const isAnomaliaPendente = anomalyDetected && aplicacao === "pendente_anomalia";
  const isAnomaliaAprovada = aplicacao === "anomalia_aprovada_ceo";
  const isAnomaliaAprovadaCalibrado = isAnomaliaAprovada && statusCalib === "calibrado";
  const isAnomaliaAprovadaFallback = isAnomaliaAprovada && statusCalib === "fallback_global";
  const isAnomaliaRejeitada = aplicacao === "anomalia_rejeitada_ceo";
  const isFallback = statusCalib === "fallback_global" && !anomalyDetected;
  const isCalibrado = statusCalib === "calibrado" && !anomalyDetected;
  const isMudanca = anomalia.motivos?.some((m) => m.includes("mudanca_estrategia"));
  const nAtual = dados.n_trades;

  let borderColor = "var(--atlas-border)";
  let bgColor = "var(--atlas-bg)";
  if (isCalibrado || isAnomaliaAprovadaCalibrado) {
    borderColor = "var(--atlas-green)";
    bgColor = "rgba(34,197,94,0.06)";
  } else if (isAnomaliaAprovadaFallback) {
    borderColor = "var(--atlas-amber)";
    bgColor = "rgba(245,158,11,0.06)";
  } else if (isAnomaliaRejeitada) {
    borderColor = "var(--atlas-border)";
    bgColor = "rgba(156,163,175,0.06)";
  } else if (isFallback) {
    borderColor = "var(--atlas-amber)";
    bgColor = "rgba(245,158,11,0.06)";
  } else if (isAnomaliaPendente) {
    borderColor = "var(--atlas-red)";
    bgColor = "rgba(239,68,68,0.06)";
  }

  async function handleAcao(acao) {
    setActionState({ loading: acao, erro: null });
    try {
      const res = await fetch(`${API_BASE}/delta-chaos/tune/confirmar-regime-anomalia`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker, regime, run_id: runId, acao }),
      });
      const body = await res.json();
      if (!res.ok) {
        setActionState({ loading: null, erro: "Erro ao confirmar — tente novamente" });
      } else {
        const resolucao = acao === "aplicar" ? "anomalia_aprovada_ceo" : "anomalia_rejeitada_ceo";
        // Backend retorna status_calibracao no nível raiz do body (campo adicionado em delta_chaos.py).
        // Contrato verificado: { status, ticker, regime, acao, estrategia, status_calibracao }
        const statusCalibRetornado = acao === "aplicar"
          ? (body?.status_calibracao ?? null)
          : null;
        onResolvido(resolucao, statusCalibRetornado);
        setActionState({ loading: null, erro: null });
      }
    } catch {
      setActionState({ loading: null, erro: "Erro ao confirmar — tente novamente" });
    }
  }

  return (
    <div style={{
      marginBottom: 10,
      padding: "8px 10px",
      background: bgColor,
      border: `1px solid ${borderColor}`,
      borderRadius: 3,
    }}>
      {/* Header: regime + badges */}
      <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: 6, marginBottom: 4 }}>
        <span style={{ fontFamily: "monospace", fontSize: 10, color: "var(--atlas-text-primary)", fontWeight: "bold" }}>
          {regime}
        </span>

        {isMudanca && (
          <span style={{
            fontFamily: "monospace", fontSize: 8, color: "#000",
            background: "var(--atlas-amber)", padding: "1px 4px", borderRadius: 2,
          }}>
            MUDANÇA
          </span>
        )}

        {isCalibrado && (
          <span style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-green)" }}>
            ✓ Aplicado automaticamente
          </span>
        )}
        {isFallback && (
          <span style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-amber)" }}>
            N insuficiente — parâmetros globais
          </span>
        )}
        {isAnomaliaPendente && (
          <span style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-red)" }}>
            ⚠ ANOMALIA — aguardando CEO
          </span>
        )}
        {isAnomaliaAprovadaCalibrado && (
          <span style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-green)" }}>
            🟢 CALIBRADO — Aprovado pelo CEO
          </span>
        )}
        {isAnomaliaAprovadaFallback && (
          <span style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-amber)" }}>
            🟡 FALLBACK — Aprovado pelo CEO
          </span>
        )}
        {isAnomaliaAprovada && !isAnomaliaAprovadaCalibrado && !isAnomaliaAprovadaFallback && (
          <span style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-green)" }}>
            ✓ Aprovado pelo CEO
          </span>
        )}
        {isAnomaliaRejeitada && (
          <span style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-text-secondary)" }}>
            ✗ Rejeitado — parâmetros do ciclo anterior mantidos
          </span>
        )}
        {isBlocked && (
          <span style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-text-secondary)" }}>
            BLOQUEADO
          </span>
        )}
      </div>

      {/* Estratégia + parâmetros calibrados */}
      {estrategia && !isBlocked && (
        <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)", marginBottom: 4 }}>
          <span style={{ color: "var(--atlas-text-primary)", fontWeight: "bold" }}>{estrategia}</span>
          {(isCalibrado || isAnomaliaAprovadaCalibrado) && (
            <>
              <span> | TP: {fmt(dados.tp_calibrado)}</span>
              <span> | Stop: {fmt(dados.stop_calibrado)}</span>
              <span style={{ color: "var(--atlas-blue)" }}> | IR: {fmt(dados.ir_calibrado, 3)}</span>
            </>
          )}
          {isAnomaliaAprovadaFallback && (
            <>
              <span> | TP: {fmt(dados.tp_calibrado)}</span>
              <span> | Stop: {fmt(dados.stop_calibrado)}</span>
            </>
          )}
          {isFallback && (
            <>
              <span> | TP: {fmt(dados.tp_calibrado)}</span>
              <span> | Stop: {fmt(dados.stop_calibrado)}</span>
            </>
          )}
          {isAnomaliaPendente && dados.tp_calibrado != null && (
            <>
              <span> | TP: {fmt(dados.tp_calibrado)}</span>
              <span> | Stop: {fmt(dados.stop_calibrado)}</span>
              {dados.ir_calibrado != null && (
                <span style={{ color: "var(--atlas-blue)" }}> | IR: {fmt(dados.ir_calibrado, 3)}</span>
              )}
            </>
          )}
        </div>
      )}

      {/* Anomalia: motivos */}
      {isAnomaliaPendente && anomalia.motivos?.length > 0 && (
        <div style={{ marginBottom: 6 }}>
          {anomalia.motivos.map((m, i) => (
            <div key={i} style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-red)", marginBottom: 1 }}>
              · {m}
            </div>
          ))}
        </div>
      )}

      {/* Anomalia: botões CEO */}
      {isAnomaliaPendente && (
        <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
          <button
            onClick={() => handleAcao("aplicar")}
            disabled={actionState.loading != null || !runId}
            title={!runId ? "run_id indisponível — re-execute calibração" : undefined}
            style={{
              padding: "3px 10px",
              background: actionState.loading === "aplicar" ? "var(--atlas-border)" : "var(--atlas-green)",
              border: "none",
              color: "#fff",
              fontFamily: "monospace",
              fontSize: 8,
              borderRadius: 2,
              cursor: (actionState.loading || !runId) ? "not-allowed" : "pointer",
              opacity: (actionState.loading || !runId) ? 0.5 : 1,
            }}
          >
            {actionState.loading === "aplicar" ? "..." : "Aplicar"}
          </button>
          <button
            onClick={() => handleAcao("rejeitar")}
            disabled={actionState.loading != null || !runId}
            title={!runId ? "run_id indisponível — re-execute calibração" : undefined}
            style={{
              padding: "3px 10px",
              background: actionState.loading === "rejeitar" ? "var(--atlas-border)" : "var(--atlas-red)",
              border: "none",
              color: "#fff",
              fontFamily: "monospace",
              fontSize: 8,
              borderRadius: 2,
              cursor: (actionState.loading || !runId) ? "not-allowed" : "pointer",
              opacity: (actionState.loading || !runId) ? 0.5 : 1,
            }}
          >
            {actionState.loading === "rejeitar" ? "..." : "Rejeitar"}
          </button>
        </div>
      )}

      {actionState.erro && (
        <div style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-red)", marginTop: 4 }}>
          {actionState.erro}
        </div>
      )}

      {/* Fallback: barra de acúmulo */}
      {isFallback && nMinimoCalib != null && nAtual != null && (
        <div style={{ marginTop: 6 }}>
          <div style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-text-secondary)", marginBottom: 2 }}>
            N atual: {nAtual} / {nMinimoCalib} trades
          </div>
          <div style={{ width: "100%", height: 3, background: "var(--atlas-border)", borderRadius: 2 }}>
            <div style={{
              width: `${Math.min((nAtual / nMinimoCalib) * 100, 100)}%`,
              height: "100%",
              background: "var(--atlas-amber)",
              borderRadius: 2,
            }} />
          </div>
        </div>
      )}

      {/* Bloqueado */}
      {isBlocked && (
        <div style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-text-secondary)", marginTop: 2 }}>
          Sem candidatos definidos para este regime
        </div>
      )}
    </div>
  );
}

export default function TuneRankingPanel({ ticker, tuneRanking, onTodosConfirmados }) {
  const [localRanking, setLocalRanking] = useState(null);
  const ranking = localRanking || tuneRanking;

  if (!ranking) {
    return (
      <div style={{ marginTop: 12, padding: "10px 12px", border: "1px solid var(--atlas-border)", borderRadius: 3, background: "var(--atlas-bg)" }}>
        <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)", lineHeight: 1.5 }}>
          TUNE v3.1 não executado para este ativo.
          <br />
          Execute a calibração para ver resultados.
        </div>
      </div>
    );
  }

  const meta = ranking._meta || {};
  const runId = meta.run_id;
  const nMinimoCalib = meta.n_minimo_calibracao;
  const concluido = ranking.concluido;
  const regimes = ranking.regimes || {};

  const aplicados = Object.values(regimes).filter(
    (r) => r.aplicacao && r.aplicacao !== "pendente_anomalia"
  );
  const anomaliasPendentes = Object.values(regimes).filter(
    (r) => r.anomalia?.detectada && !r.confirmado
  );

  function handleResolvido(regime, resolucao, statusCalibRetornado) {
    setLocalRanking((prev) => {
      const base = prev || tuneRanking;
      const novosRegimes = {
        ...(base.regimes || {}),
        [regime]: {
          ...(base.regimes?.[regime] || {}),
          confirmado: true,
          aplicacao: resolucao,
          ...(statusCalibRetornado != null ? { status_calibracao: statusCalibRetornado } : {}),
        },
      };
      const aindaPendentes = Object.values(novosRegimes).filter(
        (r) => r.anomalia?.detectada && !r.confirmado
      );
      const updated = {
        ...base,
        regimes: novosRegimes,
        aguardando_confirmacao_regimes: aindaPendentes.length > 0,
      };
      if (aindaPendentes.length === 0 && onTodosConfirmados) onTodosConfirmados();
      return updated;
    });
  }

  const runIdDisplay = runId
    ? runId.length > 20 ? `${runId.slice(0, 20)}...` : runId
    : "—";

  return (
    <div style={{ marginTop: 12 }}>
      {/* Título */}
      <div style={{
        fontFamily: "monospace", fontSize: 10,
        color: "var(--atlas-text-primary)", fontWeight: "bold", marginBottom: 8,
      }}>
        TUNE v3.1 — Eleição de Estratégia
        {meta.versao && (
          <span style={{ color: "var(--atlas-text-secondary)", fontWeight: "normal", marginLeft: 6 }}>
            v{meta.versao}
          </span>
        )}
      </div>

      {/* Header: run_id + concluido_em + contadores */}
      {concluido && (
        <div style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-text-secondary)", marginBottom: 6 }}>
          <div>run: {runIdDisplay}{meta.concluido_em && ` · ${formatDateTimeBR(meta.concluido_em)}`}</div>
          <div style={{ marginTop: 2 }}>
            <span>{aplicados.length} aplicados</span>
            {" | "}
            <span style={{ color: anomaliasPendentes.length > 0 ? "var(--atlas-amber)" : "inherit" }}>
              {anomaliasPendentes.length} anomalia{anomaliasPendentes.length !== 1 ? "s" : ""} pendente{anomaliasPendentes.length !== 1 ? "s" : ""}
            </span>
          </div>
        </div>
      )}

      {/* Status geral */}
      {!concluido && (
        <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)", marginBottom: 8 }}>
          Eleição em andamento...
        </div>
      )}
      {concluido && anomaliasPendentes.length === 0 && (
        <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-green)", marginBottom: 8 }}>
          ✓ Todos os regimes aplicados — step 3 liberado
        </div>
      )}
      {concluido && anomaliasPendentes.length > 0 && (
        <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-amber)", marginBottom: 8 }}>
          ⚠ {anomaliasPendentes.length} anomalia{anomaliasPendentes.length > 1 ? "s" : ""} detectada{anomaliasPendentes.length > 1 ? "s" : ""} — revisão CEO obrigatória
        </div>
      )}

      {/* Linhas de regime */}
      {Object.entries(regimes).map(([regime, dados]) => (
        <RegimeRow
          key={regime}
          regime={regime}
          dados={dados}
          runId={runId}
          ticker={ticker}
          nMinimoCalib={nMinimoCalib}
          onResolvido={(resolucao, statusCalibRetornado) => handleResolvido(regime, resolucao, statusCalibRetornado)}
        />
      ))}
    </div>
  );
}
