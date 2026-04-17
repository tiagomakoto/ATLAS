import React, { useEffect, useMemo, useState } from "react";
import useWebSocket from "../../hooks/useWebSocket";

const API_BASE = "http://localhost:8000";

const PULSE_ANIMATION = `
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
`;

const STEPS = [
  { id: "1_backtest_dados", label: "backtest_dados", modulo: "ORBIT" },
  { id: "2_tune", label: "tune", modulo: "TUNE" },
  { id: "3_gate_fire", label: "gate + fire", modulo: "GATE" },
];

const DEFAULT_STEPS = {
  "1_backtest_dados": { status: "idle", iniciado_em: null, concluido_em: null, erro: null },
  "2_tune": { status: "idle", iniciado_em: null, concluido_em: null, erro: null, trials_completos: 0, trials_total: 200 },
  "3_gate_fire": { status: "idle", iniciado_em: null, concluido_em: null, erro: null },
};

const STEP3_FASES = {
  GATE: "gate",
  FIRE: "fire",
};

function pad2(value) {
  return String(value).padStart(2, "0");
}

function formatDateTimeBR(value) {
  if (!value) return "";
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return "";
  return `${pad2(dt.getDate())}/${pad2(dt.getMonth() + 1)}/${dt.getFullYear()}, ${pad2(dt.getHours())}:${pad2(dt.getMinutes())}:${pad2(dt.getSeconds())}`;
}

function formatDuration(startISO, endISO) {
  if (!startISO || !endISO) return "";
  const start = new Date(startISO);
  const end = new Date(endISO);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return "";
  const totalSeconds = Math.max(Math.floor((end - start) / 1000), 0);
  if (totalSeconds < 60) return `${totalSeconds}s`;
  if (totalSeconds < 3600) {
    const m = Math.floor(totalSeconds / 60);
    const s = totalSeconds % 60;
    return `${m}m ${s}s`;
  }
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  return `${h}h ${m}m`;
}

function statusVisual(status, isNext) {
  if (status === "running") {
    return { bg: "rgba(59,130,246,0.15)", border: "var(--atlas-blue)", label: "EXECUTANDO", color: "var(--atlas-blue)" };
  }
  if (status === "done") {
    return { bg: "rgba(34,197,94,0.1)", border: "var(--atlas-green)", label: "CONCLUÍDO", color: "var(--atlas-green)" };
  }
  if (status === "error") {
    return { bg: "rgba(239,68,68,0.1)", border: "var(--atlas-red)", label: "ERRO", color: "var(--atlas-red)" };
  }
  if (status === "paused") {
    return { bg: "rgba(245,158,11,0.1)", border: "var(--atlas-amber)", label: "PAUSADO", color: "var(--atlas-amber)" };
  }
  if (isNext) {
    return { bg: "rgba(59,130,246,0.08)", border: "rgba(59,130,246,0.3)", label: "PRÓXIMO", color: "var(--atlas-blue)" };
  }
  return { bg: "rgba(156,163,175,0.1)", border: "var(--atlas-border)", label: "PENDENTE", color: "var(--atlas-text-secondary)" };
}

function buildMarkdownReport({ ticker, cycle, gateResult, fireDiag }) {
  const now = new Date().toISOString().slice(0, 10);
  const header = `# Relatório de Calibração — ${ticker} — ${cycle || "N/D"}\n**Data:** ${now}\n**Gerado por:** ATLAS\n\n---\n`;
  const gateTableHeader = "## GATE — Resultado por critério\n| Critério | Resultado | Valor |\n|----------|-----------|-------|\n";
  const gateRows = (gateResult?.criterios || [])
    .map((c) => `| ${c.id} ${c.nome} | ${c.passou ? "✓" : "✗"} | ${c.valor ?? "N/D"} |`)
    .join("\n");
  const gateResultText = `\n\n**Resultado:** ${gateResult?.resultado || "BLOQUEADO"}\n`;
  if (!fireDiag || !fireDiag.regimes || gateResult?.resultado !== "OPERAR") {
    return `${header}${gateTableHeader}${gateRows}${gateResultText}`;
  }
  const fireHeader = "\n---\n\n## FIRE — Diagnóstico histórico por regime\n| Regime | Trades | Acerto | IR | Worst trade |\n|--------|--------|--------|----|-------------|\n";
  const fireRows = fireDiag.regimes
    .map((r) => `| ${r.regime} | ${r.trades} | ${r.acerto_pct}% | ${r.ir} | ${r.worst_trade ?? "N/D"} |`)
    .join("\n");
  const estrategias = fireDiag.regimes
    .filter((r) => r.estrategia_dominante)
    .map((r) => `${r.regime} -> ${r.estrategia_dominante}`)
    .join("\n");
  const cobertura = fireDiag.cobertura || {};
  const stops = fireDiag.stops_por_regime || {};
  return `${header}${gateTableHeader}${gateRows}${gateResultText}${fireHeader}${fireRows}\n\n**Estratégia dominante por regime:**\n${estrategias || "N/D"}\n\n**Cobertura:** ${cobertura.ciclos_com_operacao ?? 0}/${cobertura.total_ciclos ?? 0} ciclos históricos com operação\n**Distribuição de stops:** ${JSON.stringify(stops)}`;
}

function downloadTextFile(filename, content) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function CalibracaoDrawer({ ticker, onClose }) {
  const [steps, setSteps] = useState(DEFAULT_STEPS);
  const [step3Fase, setStep3Fase] = useState(null);
  const [watchdogAlert, setWatchdogAlert] = useState(null);
  const [trialAtual, setTrialAtual] = useState(0);
  const [trialTotal, setTrialTotal] = useState(200);
  const [bestIr, setBestIr] = useState(0);
  const [bestTp, setBestTp] = useState(null);
  const [bestStop, setBestStop] = useState(null);
  const [ultimoEventoEm, setUltimoEventoEm] = useState(0);
  const [step2IniciadoEm, setStep2IniciadoEm] = useState(0);
  const [indexProgress, setIndexProgress] = useState({ current: 0, total: 0 });
  const [indexComplete, setIndexComplete] = useState(false);
  const [gateResult, setGateResult] = useState(null);
  const [fireDiag, setFireDiag] = useState(null);
  const [cotahistInfo, setCotahistInfo] = useState(null);
  const [showStep1Guard, setShowStep1Guard] = useState(false);

  const proximoStep = useMemo(() => {
    let ultimoDone = -1;
    for (let i = 0; i < STEPS.length; i += 1) {
      if (steps[STEPS[i].id]?.status === "done") ultimoDone = i;
    }
    for (let i = ultimoDone + 1; i < STEPS.length; i += 1) {
      if (steps[STEPS[i].id]?.status === "idle") return STEPS[i].id;
    }
    return null;
  }, [steps]);

  const step3GateStatus = useMemo(() => {
    const s3 = steps["3_gate_fire"];
    if (!s3) return "idle";
    if (s3.status === "running" && step3Fase === STEP3_FASES.GATE) return "running";
    if (s3.status === "done" && gateResult?.resultado === "OPERAR" && !fireDiag) return "done";
    if (s3.status === "done" && gateResult?.resultado !== "OPERAR") return "done";
    if (s3.status === "error") return "error";
    if (s3.status === "paused") return "paused";
    return "idle";
  }, [steps, step3Fase, gateResult, fireDiag]);

  const step3FireStatus = useMemo(() => {
    const s3 = steps["3_gate_fire"];
    if (!s3) return "idle";
    if (s3.status === "running" && step3Fase === STEP3_FASES.FIRE) return "running";
    if (fireDiag) return "done";
    if (s3.status === "done" && gateResult?.resultado === "OPERAR" && !fireDiag) return "idle";
    if (s3.status === "error") return "error";
    return "idle";
  }, [steps, step3Fase, gateResult, fireDiag]);

  useEffect(() => {
    let mounted = true;
    async function loadInitial() {
      try {
        const [statusRes, cotahistRes] = await Promise.all([
          fetch(`${API_BASE}/delta-chaos/calibracao/${ticker}`),
          fetch(`${API_BASE}/ativos/${ticker}/cotahist-recente`),
        ]);
        if (statusRes.ok) {
          const data = await statusRes.json();
          if (!mounted) return;

          const persistedSteps = data?.steps || {};
          const step1Data = persistedSteps["1_backtest_dados"] || {};
          const step2Data = persistedSteps["2_tune"] || {};
          const step3Data = persistedSteps["3_gate_fire"] || persistedSteps["3_backtest_gate"] || {};

          setSteps({
            "1_backtest_dados": { ...DEFAULT_STEPS["1_backtest_dados"], ...step1Data },
            "2_tune": { ...DEFAULT_STEPS["2_tune"], ...step2Data },
            "3_gate_fire": { ...DEFAULT_STEPS["3_gate_fire"], ...step3Data },
          });

          if (step3Data.status === "running") {
            if (data?.gate_resultado && !data?.fire_diagnostico) {
              setStep3Fase(STEP3_FASES.FIRE);
            } else if (!data?.gate_resultado) {
              setStep3Fase(STEP3_FASES.GATE);
            }
          }

if (data?.gate_resultado) setGateResult(data.gate_resultado);
      if (data?.fire_diagnostico) setFireDiag(data.fire_diagnostico);
      if (data?.steps?.["2_tune"]?.iniciado_em) setStep2IniciadoEm(new Date(data.steps["2_tune"].iniciado_em).getTime());
      if (data?.ultimo_evento_em) setUltimoEventoEm(new Date(data.ultimo_evento_em).getTime());

      // Fallback: se step 3 está done mas não tem gateResult, buscar via endpoint
      const step3Status = step3Data?.status || persistedSteps["3_gate_fire"]?.status;
      if (step3Status === "done" && !data?.gate_resultado) {
        try {
          const gateRes = await fetch(`${API_BASE}/ativos/${ticker}/gate-resultado`);
          if (gateRes.ok) setGateResult(await gateRes.json());
        } catch (e) { console.error("Erro gate-resultado:", e); }
      }
      // Fallback: se GATE aprovou mas não tem fireDiag, buscar via endpoint
      if (step3Status === "done" && data?.gate_resultado?.resultado === "OPERAR" && !data?.fire_diagnostico) {
        try {
          const fireRes = await fetch(`${API_BASE}/ativos/${ticker}/fire-diagnostico`);
          if (fireRes.ok) setFireDiag(await fireRes.json());
        } catch (e) { console.error("Erro fire-diagnostico:", e); }
      }
        }
        if (cotahistRes.ok) {
          const info = await cotahistRes.json();
          if (!mounted) return;
          setCotahistInfo(info);
          setShowStep1Guard(Boolean(info?.dados_recentes));
        }
      } catch (error) {
        console.error("Erro ao carregar calibração:", error);
      }
    }
    loadInitial();
    return () => { mounted = false; };
  }, [ticker]);

  useEffect(() => {
    if (!ultimoEventoEm || !step2IniciadoEm) return undefined;
    const interval = setInterval(() => {
      const mins = Math.floor((Date.now() - ultimoEventoEm) / 60000);
      if (steps["2_tune"]?.status === "running" && mins >= 5) {
        setWatchdogAlert(`Sem sinal há ${mins}min — processo pode ter sido interrompido`);
      } else if (steps["2_tune"]?.status === "running" && mins < 5) {
        setWatchdogAlert(null);
      }
    }, 60000);
    return () => clearInterval(interval);
  }, [ultimoEventoEm, step2IniciadoEm, steps]);

  async function refreshGateResult() {
    try {
      const res = await fetch(`${API_BASE}/ativos/${ticker}/gate-resultado`);
      if (res.ok) {
        const data = await res.json();
        setGateResult(data);
      }
    } catch (error) {
      console.error("Erro gate-resultado:", error);
    }
  }

  async function refreshFireDiag() {
    try {
      const res = await fetch(`${API_BASE}/ativos/${ticker}/fire-diagnostico`);
      if (res.ok) setFireDiag(await res.json());
    } catch (error) {
      console.error("Erro fire-diagnostico:", error);
    }
  }

  const wsUrl = `ws://${window.location.hostname}:${window.location.port || "8000"}/ws/events`;
  useWebSocket(wsUrl, (evento) => {
    const modulo = evento?.data?.modulo;
    setUltimoEventoEm(Date.now());

    if (evento?.type === "dc_module_start") {
      if (modulo === "ORBIT" || modulo === "TAPE" || modulo === "REFLECT") {
        setSteps((prev) => ({
          ...prev,
          "1_backtest_dados": {
            ...prev["1_backtest_dados"],
            status: "running",
            iniciado_em: evento?.data?.timestamp || new Date().toISOString(),
          },
        }));
      }
      if (modulo === "TUNE") {
        setSteps((prev) => ({
          ...prev,
          "2_tune": {
            ...prev["2_tune"],
            status: "running",
            iniciado_em: evento?.data?.timestamp || new Date().toISOString(),
          },
        }));
        setStep2IniciadoEm(Date.now());
        setIndexProgress({ current: 0, total: 0 });
        setIndexComplete(false);
        setBestTp(null);
        setBestStop(null);
      }
      if (modulo === "GATE") {
        setStep3Fase(STEP3_FASES.GATE);
        setSteps((prev) => ({
          ...prev,
          "3_gate_fire": {
            ...prev["3_gate_fire"],
            status: "running",
            iniciado_em: prev["3_gate_fire"]?.iniciado_em || evento?.data?.timestamp || new Date().toISOString(),
          },
        }));
      }
      if (modulo === "FIRE") {
        setStep3Fase(STEP3_FASES.FIRE);
      }
    }

    if (evento?.type === "dc_module_complete") {
      if (modulo === "ORBIT" || modulo === "TAPE" || modulo === "REFLECT") {
        const ok = evento?.data?.status === "ok";
        setSteps((prev) => ({
          ...prev,
          "1_backtest_dados": {
            ...prev["1_backtest_dados"],
            status: ok ? "done" : "error",
            concluido_em: evento?.data?.timestamp || new Date().toISOString(),
            erro: ok ? null : evento?.data?.erro,
          },
        }));
      }
      if (modulo === "TUNE") {
        const ok = evento?.data?.status === "ok";
        setSteps((prev) => ({
          ...prev,
          "2_tune": {
            ...prev["2_tune"],
            status: ok ? "done" : "error",
            concluido_em: evento?.data?.timestamp || new Date().toISOString(),
            erro: ok ? null : evento?.data?.erro,
          },
        }));
      }
      if (modulo === "GATE") {
        const ok = evento?.data?.status === "ok";
        const payloadGate = evento?.data?.gate_resultado || null;
        if (payloadGate) setGateResult(payloadGate);
        const gateAprovado = payloadGate?.resultado === "OPERAR";

        if (ok && gateAprovado) {
          setSteps((prev) => ({
            ...prev,
            "3_gate_fire": { ...prev["3_gate_fire"], status: "running" },
          }));
          setStep3Fase(STEP3_FASES.FIRE);
        } else if (ok && !gateAprovado) {
          setSteps((prev) => ({
            ...prev,
            "3_gate_fire": {
              ...prev["3_gate_fire"],
              status: "done",
              concluido_em: evento?.data?.timestamp || new Date().toISOString(),
            },
          }));
          setStep3Fase(null);
        } else {
          setSteps((prev) => ({
            ...prev,
            "3_gate_fire": {
              ...prev["3_gate_fire"],
              status: "error",
              concluido_em: evento?.data?.timestamp || new Date().toISOString(),
              erro: evento?.data?.erro,
            },
          }));
          setStep3Fase(null);
        }
        if (ok) refreshGateResult();
      }
      if (modulo === "FIRE") {
        const ok = evento?.data?.status === "ok";
        if (evento?.data?.fire_diagnostico) setFireDiag(evento.data.fire_diagnostico);
        setSteps((prev) => ({
          ...prev,
          "3_gate_fire": {
            ...prev["3_gate_fire"],
            status: ok ? "done" : "error",
            concluido_em: evento?.data?.timestamp || new Date().toISOString(),
            erro: ok ? null : evento?.data?.erro,
          },
        }));
        setStep3Fase(null);
        if (ok) refreshFireDiag();
      }
    }

    if (evento?.type === "dc_tune_progress") {
      const d = evento.data || {};
      if (d.trial != null) setTrialAtual(d.trial);
      if (d.total != null) setTrialTotal(d.total);
      if (d.ir != null) setBestIr(d.ir);
      if (d.best_tp != null) setBestTp(d.best_tp);
      if (d.best_stop != null) setBestStop(d.best_stop);
    }

    if (evento?.type === "dc_tune_index_start") {
      setIndexProgress({ current: evento?.data?.current || 0, total: evento?.data?.total || 0 });
      setIndexComplete(false);
    }
    if (evento?.type === "dc_tune_index_progress") {
      setIndexProgress({ current: evento?.data?.current || 0, total: evento?.data?.total || 0 });
      setIndexComplete(false);
    }
    if (evento?.type === "dc_tune_index_complete") {
      setIndexComplete(true);
    }

    if (evento?.type === "terminal_log") {
      const message = evento?.data?.message || "";
      const indexRegex = /TUNE \[([A-Z0-9]+)\] indexando dias: ([\d,]+)\/([\d,]+)/;
      const match = message.match(indexRegex);
      if (match) {
        const current = parseInt(match[2].replace(/,/g, ""), 10);
        const total = parseInt(match[3].replace(/,/g, ""), 10);
        setIndexProgress({ current, total });
        setIndexComplete(false);
      }
      if (message.includes("pré-cômputo concluído")) {
        setIndexComplete(true);
      }
    }
  });

  function getStepLabel(key) {
    const step = STEPS.find((s) => s.id === key);
    return step ? step.label : key;
  }

  function getStepDescription(key) {
    const status = steps[key]?.status || "idle";
    if (status === "running") return "Em execução";
    if (status === "done") return "Concluído";
    if (status === "error") return `Falhou: ${steps[key]?.erro || "erro desconhecido"}`;
    if (status === "paused") return "Pausado — clique em retomar";
    if (key === "2_tune" && proximoStep === key) return "Optuna 200 trials · estimativa 4–8h";
    return "Aguardando início";
  }

  function getStepDuration(key) {
    const s = steps[key];
    if (!s || s.status !== "done" || !s.concluido_em) return "";
    const dt = formatDateTimeBR(s.concluido_em);
    const duration = formatDuration(s.iniciado_em, s.concluido_em);
    return duration ? `Concluído ${dt} · duração: ${duration}` : `Concluído ${dt}`;
  }

  async function handleIniciar() {
    try {
      const res = await fetch(`${API_BASE}/delta-chaos/calibracao/iniciar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker, confirm: true, description: "Iniciar calibração" }),
      });
      if (!res.ok) {
        setSteps((prev) => ({
          ...prev,
          "1_backtest_dados": { ...prev["1_backtest_dados"], status: "error" },
        }));
      } else {
        setShowStep1Guard(false);
      }
    } catch (error) {
      console.error("Erro ao iniciar calibração:", error);
      setSteps((prev) => ({
        ...prev,
        "1_backtest_dados": { ...prev["1_backtest_dados"], status: "error" },
      }));
    }
  }

  function handleSkipStep1() {
    const now = new Date().toISOString();
    setShowStep1Guard(false);
    setSteps((prev) => ({
      ...prev,
      "1_backtest_dados": { ...prev["1_backtest_dados"], status: "done", iniciado_em: now, concluido_em: now },
    }));
  }

  async function handleRetomar() {
    try {
      await fetch(`${API_BASE}/delta-chaos/calibracao/${ticker}/retomar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
    } catch (error) {
      console.error("Erro ao retomar:", error);
    }
  }

  async function handleConfirmarOperar() {
    try {
      await fetch(`${API_BASE}/ativos/${ticker}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "OPERAR" }),
      });
      onClose();
    } catch (error) {
      console.error("Erro ao confirmar OPERAR:", error);
    }
  }

  function handleExport() {
    const now = new Date().toISOString().slice(0, 10);
    const cycle = gateResult?.ciclo || now.slice(0, 7);
    const blocked = gateResult?.resultado !== "OPERAR";
    const filename = blocked
      ? `GATE_${ticker}_${cycle}_${now}_BLOQUEADO.md`
      : `CALIBRACAO_${ticker}_${cycle}_${now}.md`;
    const markdown = buildMarkdownReport({
      ticker,
      cycle,
      gateResult,
      fireDiag: blocked ? null : fireDiag,
    });
    downloadTextFile(filename, markdown);
  }

  async function handleExportarRelatorioBackend() {
    try {
      const res = await fetch(`${API_BASE}/delta-chaos/calibracao/${ticker}/exportar-relatorio`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (res.ok) {
        const data = await res.json();
        if (data.caminho) {
          const filename = data.arquivo;
          const markdown = buildMarkdownReport({
            ticker,
            cycle: gateResult?.ciclo || new Date().toISOString().slice(0, 7),
            gateResult: data.gate_resultado,
            fireDiag: data.fire_diagnostico,
          });
          downloadTextFile(filename, markdown);
        }
      }
    } catch (error) {
      console.error("Erro ao exportar relatório via backend:", error);
      handleExport();
    }
  }

  function elapsedForStep2() {
    if (!step2IniciadoEm) return "0s";
    const diff = Date.now() - step2IniciadoEm;
    const s = Math.floor(diff / 1000) % 60;
    const m = Math.floor(diff / 60000) % 60;
    const h = Math.floor(diff / 3600000);
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  }

  function estimatedForStep2() {
    if (!step2IniciadoEm || trialAtual <= 0 || trialTotal <= 0) return "0s";
    const avgMs = (Date.now() - step2IniciadoEm) / trialAtual;
    const rem = Math.max(trialTotal - trialAtual, 0) * avgMs;
    const s = Math.floor(rem / 1000) % 60;
    const m = Math.floor(rem / 60000) % 60;
    const h = Math.floor(rem / 3600000);
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  }

  const gateBlocked = gateResult && gateResult.resultado !== "OPERAR";
  const concluidoComFire = gateResult?.resultado === "OPERAR" && steps["3_gate_fire"]?.status === "done" && fireDiag;

  // Renderiza card de um step
  function renderStepCard(stepId) {
    const status = steps[stepId]?.status || "idle";
    const isNext = status === "idle" && proximoStep === stepId;
    const visual = statusVisual(status, isNext);
    const stepDone = status === "done";
    const icon = status === "done" ? "●" : status === "running" ? "⟳" : status === "error" ? "×" : status === "paused" ? "⏸" : "○";

    return (
      <div
        key={stepId}
        style={{
          display: "flex",
          alignItems: "flex-start",
          marginBottom: 8,
          padding: "8px 12px",
          background: visual.bg,
          border: `1px solid ${visual.border}`,
          borderRadius: 2,
          opacity: status === "idle" && !isNext ? 0.7 : 1,
        }}
      >
        <span style={{
          fontSize: 14,
          color: visual.color,
          fontWeight: "bold",
          marginRight: 8,
          animation: status === "running" || isNext ? "pulse 1s infinite" : "none",
        }}>
          {icon}
        </span>
        <div style={{ width: "100%" }}>
          <div style={{ fontFamily: "monospace", fontSize: 11, color: visual.color, fontWeight: "bold" }}>
            {visual.label}
          </div>
          <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)" }}>
            {getStepLabel(stepId)}
          </div>
          <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)" }}>
            {getStepDescription(stepId)}
            {stepDone && getStepDuration(stepId) ? ` · ${getStepDuration(stepId)}` : ""}
          </div>

          {/* Step 1 guard */}
          {stepId === "1_backtest_dados" && showStep1Guard && status === "idle" && cotahistInfo?.data_ultimo_cotahist && (
            <div style={{ marginTop: 8, border: "1px solid var(--atlas-amber)", background: "rgba(245,158,11,0.08)", padding: 8, borderRadius: 4 }}>
              <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-amber)", marginBottom: 8 }}>
                ⚠ Dados atualizados em {formatDateTimeBR(cotahistInfo.data_ultimo_cotahist)} — deseja rodar mesmo assim?
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  onClick={handleSkipStep1}
                  style={{ flex: 1, padding: "5px 8px", background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", color: "var(--atlas-text-secondary)", fontFamily: "monospace", fontSize: 9, borderRadius: 2, cursor: "pointer" }}
                >
                  Pular step 1
                </button>
                <button
                  onClick={handleIniciar}
                  style={{ flex: 1, padding: "5px 8px", background: "var(--atlas-blue)", border: "none", color: "#fff", fontFamily: "monospace", fontSize: 9, borderRadius: 2, cursor: "pointer" }}
                >
                  Rodar mesmo assim
                </button>
              </div>
            </div>
          )}

          {/* Step 2 progresso TUNE */}
          {stepId === "2_tune" && status === "running" && (
            <div style={{ marginTop: 8 }}>
              {!indexComplete && (
                <div style={{ marginBottom: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)" }}>
                      Indexando dias: {indexProgress.current.toLocaleString("pt-BR")} / {indexProgress.total.toLocaleString("pt-BR")}
                    </span>
                    <span style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)" }}>
                      {indexProgress.total > 0 ? `${Math.round((indexProgress.current / indexProgress.total) * 100)}%` : "0%"}
                    </span>
                  </div>
                  <div style={{ width: "100%", height: 6, background: "var(--atlas-border)", borderRadius: 4, overflow: "hidden" }}>
                    <div style={{ width: `${indexProgress.total > 0 ? (indexProgress.current / indexProgress.total) * 100 : 0}%`, height: "100%", background: "var(--atlas-blue)" }} />
                  </div>
                </div>
              )}
              {indexComplete && (
                <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-green)", marginBottom: 8 }}>
                  {indexProgress.total.toLocaleString("pt-BR")} dias indexados
                </div>
              )}
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)" }}>
                  {trialAtual} / {trialTotal} trials
                </span>
                <span style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)" }}>
                  IR: {Number(bestIr || 0).toFixed(3)}
                </span>
              </div>
              <div style={{ width: "100%", height: 6, background: "var(--atlas-border)", borderRadius: 4, overflow: "hidden" }}>
                <div style={{ width: `${trialTotal > 0 ? (trialAtual / trialTotal) * 100 : 0}%`, height: "100%", background: "var(--atlas-blue)" }} />
              </div>
              {(bestTp != null || bestStop != null) && (
                <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-blue)", marginTop: 4 }}>
                  TP {bestTp != null ? Number(bestTp).toFixed(2) : "--"} | STOP {bestStop != null ? Number(bestStop).toFixed(2) : "--"}
                </div>
              )}
              <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)", marginTop: 4 }}>
                Tempo decorrido {elapsedForStep2()} (est. restante {estimatedForStep2()})
              </div>
            </div>
          )}

          {/* Step 2 paused */}
          {stepId === "2_tune" && status === "paused" && (
            <button
              onClick={handleRetomar}
              style={{ marginTop: 8, padding: "4px 10px", background: "var(--atlas-blue)", border: "none", color: "#fff", fontFamily: "monospace", fontSize: 9, borderRadius: 2, cursor: "pointer" }}
            >
              Retomar
            </button>
          )}

          {/* Step 3 GATE + FIRE */}
          {stepId === "3_gate_fire" && (
            <>
              {/* Sub-fases GATE / FIRE quando step3 está rodando */}
              {status === "running" && (
                <div style={{ marginTop: 8, marginLeft: 20, borderLeft: "2px solid var(--atlas-border)", paddingLeft: 12 }}>
                  <div style={{ marginBottom: 4 }}>
                    <span style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)", marginRight: 6 }}>GATE:</span>
                    <span style={{
                      fontFamily: "monospace",
                      fontSize: 9,
                      color: step3GateStatus === "running" ? "var(--atlas-blue)" : step3GateStatus === "done" ? "var(--atlas-green)" : "var(--atlas-text-secondary)",
                      fontWeight: step3GateStatus === "running" ? "bold" : "normal",
                    }}>
                      {step3GateStatus === "running" ? "⟳ executando..." : step3GateStatus === "done" ? "✓ ok" : "○ aguardando"}
                    </span>
                  </div>
                  <div>
                    <span style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)", marginRight: 6 }}>FIRE:</span>
                    <span style={{
                      fontFamily: "monospace",
                      fontSize: 9,
                      color: step3FireStatus === "running" ? "#a855f7" : step3FireStatus === "done" ? "var(--atlas-green)" : "var(--atlas-text-secondary)",
                      fontWeight: step3FireStatus === "running" ? "bold" : "normal",
                    }}>
                      {step3FireStatus === "running" ? "⟳ executando..." : step3FireStatus === "done" ? "✓ ok" : "○ aguardando"}
                    </span>
                  </div>
                </div>
              )}

              {/* GATE critérios */}
              {gateResult && (
                <div style={{ marginTop: 8, border: "1px solid var(--atlas-border)", background: "var(--atlas-surface)", borderRadius: 4, padding: 8 }}>
                  <div style={{ fontFamily: "monospace", fontSize: 10, color: "var(--atlas-text-primary)", marginBottom: 6 }}>GATE</div>
                  {(gateResult.criterios || []).map((c) => (
                    <div key={c.id} style={{ display: "flex", justifyContent: "space-between", fontFamily: "monospace", fontSize: 9, color: c.passou ? "var(--atlas-green)" : "var(--atlas-red)" }}>
                      <span>{c.id} {c.nome}</span>
                      <span>{c.passou ? "✓" : "✗"} {c.valor ?? "N/D"}</span>
                    </div>
                  ))}
                  <div style={{ marginTop: 6, fontFamily: "monospace", fontSize: 10, color: gateResult.resultado === "OPERAR" ? "var(--atlas-green)" : "var(--atlas-red)", fontWeight: "bold" }}>
                    RESULTADO: {gateResult.resultado === "OPERAR" ? "✓ OPERAR" : "✗ BLOQUEADO"}
                  </div>
                </div>
              )}

              {/* FIRE diagnóstico */}
              {gateResult?.resultado === "OPERAR" && (
                <>
                  <div style={{ marginTop: 8, border: "1px solid var(--atlas-border)", background: "var(--atlas-surface)", borderRadius: 4, padding: 8 }}>
                    <div style={{ fontFamily: "monospace", fontSize: 10, color: "var(--atlas-text-primary)", marginBottom: 6 }}>FIRE — Diagnóstico histórico</div>
                    {fireDiag?.regimes?.length ? (
                      <>
{fireDiag.regimes.map((r) => (
              <div key={r.regime} style={{ display: "grid", gridTemplateColumns: "1fr .6fr .6fr .5fr .7fr", gap: 4, fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)", marginBottom: 2 }}>
                <span>{r.regime}</span>
                <span>{r.trades}t</span>
                <span>{r.acerto_pct}%</span>
                <span>IR {r.ir?.toFixed(2)}</span>
                <span style={{ color: r.worst_trade ? "var(--atlas-red)" : "inherit" }}>{r.worst_trade ? `W: ${r.worst_trade}` : "-"}</span>
              </div>
            ))}
            {fireDiag.regimes.some((r) => r.estrategia_dominante) && (
              <div style={{ marginTop: 6, fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)" }}>
                <span style={{ color: "var(--atlas-blue)", fontWeight: "bold" }}>Estrat.: </span>
                {fireDiag.regimes.filter((r) => r.estrategia_dominante).map((r) => `${r.regime}→${r.estrategia_dominante}`).join(" | ")}
              </div>
            )}
<div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)", marginTop: 6 }}>
            Cobertura: {fireDiag?.cobertura?.ciclos_com_operacao ?? 0}/{fireDiag?.cobertura?.total_ciclos ?? 0} ciclos
          </div>
          {fireDiag?.stops_por_regime && Object.keys(fireDiag.stops_por_regime).length > 0 && (
            <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)", marginTop: 2 }}>
              <span style={{ color: "var(--atlas-amber)" }}>Stops: </span>
              {Object.entries(fireDiag.stops_por_regime).map(([regime, count]) => `${regime}: ${count}`).join(" | ")}
            </div>
          )}
                      </>
                    ) : (
                      <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)" }}>Aguardando diagnóstico FIRE...</div>
                    )}
                  </div>
                </>
              )}

              {/* Botão exportar */}
              {(gateResult || fireDiag) && (
                <button
                  onClick={handleExportarRelatorioBackend}
                  style={{ marginTop: 8, width: "100%", padding: "6px 10px", background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", color: "var(--atlas-text-secondary)", fontFamily: "monospace", fontSize: 9, borderRadius: 2, cursor: "pointer" }}
                >
                  Exportar relatório .md
                </button>
              )}
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <>
      <div
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          width: "400px",
          height: "100%",
          background: "var(--atlas-surface)",
          borderLeft: "1px solid var(--atlas-border)",
          zIndex: 1000,
          padding: 16,
          overflowY: "auto",
          boxShadow: "-5px 0 15px rgba(0,0,0,0.1)",
        }}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h3 style={{ margin: 0, fontFamily: "monospace", fontSize: 14, color: "var(--atlas-text-primary)" }}>
            CALIBRAÇÃO — {ticker}
          </h3>
          <button
            onClick={onClose}
            style={{ background: "transparent", border: "none", fontSize: 16, color: "var(--atlas-text-secondary)", cursor: "pointer" }}
          >
            ×
          </button>
        </div>

        {/* Watchdog alert */}
        {watchdogAlert && (
          <div style={{ background: "rgba(245,158,11,0.2)", color: "var(--atlas-text-primary)", padding: "8px 12px", borderRadius: 4, marginBottom: 16, fontSize: 10, fontFamily: "monospace" }}>
            {watchdogAlert}
          </div>
        )}

        {/* Conclusão com FIRE */}
        {concluidoComFire && (
          <div style={{ border: "1px solid var(--atlas-green)", background: "rgba(34,197,94,0.08)", padding: 12, marginBottom: 12, borderRadius: 4 }}>
            <div style={{ fontFamily: "monospace", fontSize: 12, color: "var(--atlas-green)", fontWeight: "bold", marginBottom: 8 }}>
              ✓ CALIBRAÇÃO CONCLUÍDA — {ticker}
            </div>
            <div style={{ fontFamily: "monospace", fontSize: 10, color: "var(--atlas-text-secondary)", marginBottom: 10 }}>
              {ticker} aprovado pelo GATE. Confirmar entrada em OPERAR?
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                onClick={handleConfirmarOperar}
                style={{ flex: 1, padding: "6px 10px", background: "var(--atlas-green)", border: "none", color: "#fff", fontFamily: "monospace", fontSize: 10, borderRadius: 2, cursor: "pointer" }}
              >
                Confirmar OPERAR
              </button>
              <button
                onClick={onClose}
                style={{ flex: 1, padding: "6px 10px", background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", color: "var(--atlas-text-secondary)", fontFamily: "monospace", fontSize: 10, borderRadius: 2, cursor: "pointer" }}
              >
                Manter MONITORAR
              </button>
            </div>
          </div>
        )}

        {/* GATE bloqueado */}
        {gateBlocked && (
          <div style={{ border: "1px solid var(--atlas-red)", background: "rgba(239,68,68,0.08)", padding: 12, marginBottom: 12, borderRadius: 4 }}>
            <div style={{ fontFamily: "monospace", fontSize: 12, color: "var(--atlas-red)", fontWeight: "bold", marginBottom: 8 }}>
              ✗ GATE BLOQUEADO — {ticker}
            </div>
            <div style={{ fontFamily: "monospace", fontSize: 10, color: "var(--atlas-text-secondary)", marginBottom: 10 }}>
              Critério(s) reprovado(s): {(gateResult?.falhas || []).join(", ") || "N/D"}
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                onClick={handleExportarRelatorioBackend}
                style={{ flex: 1, padding: "6px 10px", background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", color: "var(--atlas-text-secondary)", fontFamily: "monospace", fontSize: 10, borderRadius: 2, cursor: "pointer" }}
              >
                Exportar relatório GATE
              </button>
              <button
                onClick={onClose}
                style={{ flex: 1, padding: "6px 10px", background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", color: "var(--atlas-text-secondary)", fontFamily: "monospace", fontSize: 10, borderRadius: 2, cursor: "pointer" }}
              >
                Fechar
              </button>
            </div>
          </div>
        )}

        {/* Cards de steps */}
        <div style={{ background: "var(--atlas-bg)", padding: 12, borderRadius: 4, marginBottom: 16 }}>
          {STEPS.map((step) => renderStepCard(step.id))}
        </div>

        {/* Botão iniciar (quando step 1 está idle e sem guard) */}
        {steps["1_backtest_dados"]?.status === "idle" && !showStep1Guard && (
          <button
            onClick={handleIniciar}
            style={{ width: "100%", padding: "8px 16px", background: "var(--atlas-blue)", border: "none", color: "#fff", fontFamily: "monospace", fontSize: 11, borderRadius: 4, cursor: "pointer", marginBottom: 8 }}
          >
            Iniciar calibração
          </button>
        )}
      </div>
      <style>{PULSE_ANIMATION}</style>
    </>
  );
}