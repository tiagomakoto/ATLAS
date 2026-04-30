import React, { useEffect, useMemo, useState } from "react";
import useWebSocket from "../../hooks/useWebSocket";
import TuneRankingPanel from "./TuneRankingPanel";

const API_BASE = "http://localhost:8000";

const PULSE_ANIMATION = `
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
`;

const STEPS = [
  { id: "1_backtest_dados", label: "backtest_dados", name: "Integridade de dados", modulo: "ORBIT" },
  { id: "2_tune", label: "tune", name: "Parametrização", modulo: "TUNE" },
  { id: "3_gate_fire", label: "gate + fire", name: "Validação", modulo: "GATE" },
];

const DEFAULT_STEPS = {
  "1_backtest_dados": { status: "idle", iniciado_em: null, concluido_em: null, erro: null },
  "2_tune": { status: "idle", iniciado_em: null, concluido_em: null, erro: null, trials_completos: 0, trials_total: 150 },
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

function buildMarkdownReport({ ticker, cycle, steps, bestTp, bestStop, bestIr, gateResult, gateError, fireDiag, tuneStats, gateStats, tuneRanking }) {
  const now = new Date().toISOString().slice(0, 10);
  const header = `# Relatório de Calibração — ${ticker} — ${cycle || "N/D"}\n**Data:** ${now}\n**Gerado por:** ATLAS\n\n---\n`;

  // Placeholder "—" (U+2014) é deliberado para as tabelas novas abaixo, conforme
  // SPEC do patch. As seções legadas continuam usando "–" (U+2013) — não unificar.
  const fmt = (value, kind = "raw") => {
    if (value == null) return "—";
    switch (kind) {
      case "currency":
        return Number(value).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      case "percent":
        return `${Number(value).toFixed(2)}%`;
      case "int":
        return Number(value).toLocaleString("pt-BR");
      case "float":
        return Number(value).toFixed(4);
      default:
        return String(value);
    }
  };

  // Step 1 — ORBIT / TAPE / REFLECT
  const s1 = steps?.["1_backtest_dados"] || {};
  const s1Status = s1.status === "done" ? "✓ ok" : s1.status === "error" ? `✗ erro: ${s1.erro || "?"}` : "–";
  const s1Dur = formatDuration(s1.iniciado_em, s1.concluido_em);
  const step1Section = `## Step 1 — Integridade de dados (ORBIT / TAPE / REFLECT)\n**Status:** ${s1Status}${s1Dur ? ` · duração: ${s1Dur}` : ""}\n`;

  // Step 2 — TUNE
  const s2 = steps?.["2_tune"] || {};
  const s2Status = s2.status === "done" ? "✓ ok" : s2.status === "error" ? `✗ erro: ${s2.erro || "?"}` : "–";
  const s2Dur = formatDuration(s2.iniciado_em, s2.concluido_em);
  const tuneParams = (bestTp != null || bestStop != null)
    ? `**Parâmetros:** TP ${bestTp != null ? Number(bestTp).toFixed(2) : "–"} | STOP ${bestStop != null ? Number(bestStop).toFixed(2) : "–"}${bestIr ? ` | IR ${Number(bestIr).toFixed(4)}` : ""}\n`
    : "";
  const step2Section = `\n## Step 2 — Parametrização (TUNE)\n**Status:** ${s2Status}${s2Dur ? ` · duração: ${s2Dur}` : ""}\n${tuneParams}`;

  const tuneQualidadeSection = tuneStats ? `
## Qualidade da otimização
| Campo | Valor |
|---|---|
| IR válido (janela teste) | ${fmt(tuneStats.ir_valido, "float")} |
| N trades na janela | ${fmt(tuneStats.n_trades, "int")} |
| Confiança | ${fmt(tuneStats.confianca_n)} |
| Janela de teste | ${fmt(tuneStats.janela_anos)} anos (${fmt(tuneStats.ano_teste_ini)}–hoje) |
| Trials rodados | ${fmt(tuneStats.trials, "int")} |
| Ciclos mascarados REFLECT | ${fmt(tuneStats.reflect_mask, "int")} |
| Acerto % | ${fmt(tuneStats.acerto_pct, "percent")} |
| P&L médio por trade | R$${fmt(tuneStats.pnl_medio, "currency")} |
| P&L mediana por trade | R$${fmt(tuneStats.pnl_mediana, "currency")} |
| Pior trade | R$${fmt(tuneStats.pnl_pior, "currency")} |
| Stops totais | ${fmt(tuneStats.n_stops, "int")} |
` : "";

  // Step 3 — GATE
  const s3 = steps?.["3_gate_fire"] || {};
  const s3Status = s3.status === "done" ? "✓ ok" : s3.status === "error" ? `✗ erro: ${s3.erro || "?"}` : "–";
  const s3Dur = formatDuration(s3.iniciado_em, s3.concluido_em);
  const gateTableHeader = `\n## Step 3 — Validação (GATE + FIRE)\n**Status:** ${s3Status}${s3Dur ? ` · duração: ${s3Dur}` : ""}\n### GATE — Resultado por critério\n| Critério | Resultado | Valor |\n|----------|-----------|-------|\n`;
  let gateSection;
  if (!gateResult) {
    const errMsg = gateError ? `> GATE falhou com erro: \`${gateError}\`\n` : "> GATE não retornou dados.\n";
    gateSection = `${gateTableHeader}${errMsg}\n**Resultado:** ERRO\n`;
  } else {
    const criterios = gateResult.criterios || [];
    const gateRows = criterios.length
      ? criterios.map((c) => `| ${c.id} ${c.nome || ""} | ${c.passou ? "✓" : "✗"} | ${c.valor ?? "N/D"} |`).join("\n")
      : "";
    const criteriosVazios = !criterios.length ? "\n> Critérios não disponíveis.\n" : "";
    const resultadoLabel = gateResult.resultado === "OPERAR" ? "✓ OPERAR" : "✗ BLOQUEADO";
    gateSection = `${gateTableHeader}${gateRows}${criteriosVazios}\n\n**Resultado:** ${resultadoLabel}\n`;
  }

  const gateDiagSection = gateStats ? `
## Diagnóstico quantitativo
| Campo | Valor |
|---|---|
| N trades válidos | ${fmt(gateStats.n_trades_valido, "int")} |
| P&L total janela | R$${fmt(gateStats.pnl_total, "currency")} |
| P&L médio por trade | R$${fmt(gateStats.pnl_medio, "currency")} |
| P&L mediana | R$${fmt(gateStats.pnl_mediana, "currency")} |
| Pior trade | R$${fmt(gateStats.pnl_pior, "currency")} |
| Drawdown máximo | R$${fmt(gateStats.dd_max, "currency")} |
| Stops consecutivos máx | ${fmt(gateStats.stops_seguidos, "int")} |
` : "";

  const estrategiaSection = gateStats?.estrategia_por_regime ? `
## Estratégia por regime (janela válida)
| Regime | Estratégia |
|---|---|
${Object.entries(gateStats.estrategia_por_regime)
  .map(([regime, estrategia]) => `| ${regime} | ${fmt(estrategia)} |`)
  .join("\n")}
` : "";

  // Step 3 — FIRE (somente se GATE aprovou)
  let fireSection = "";
  if (fireDiag?.regimes?.length && gateResult?.resultado === "OPERAR") {
    const fireHeader = "\n### FIRE — Diagnóstico histórico por regime\n| Regime | Trades | Acerto | IR | Worst trade |\n|--------|--------|--------|----|-------------|\n";
    const fireRows = fireDiag.regimes
      .map((r) => `| ${r.regime} | ${r.trades} | ${r.acerto_pct}% | ${r.ir} | ${r.worst_trade ?? "N/D"} |`)
      .join("\n");
    const estrategias = fireDiag.regimes
      .filter((r) => r.estrategia_dominante)
      .map((r) => `${r.regime} -> ${r.estrategia_dominante}`)
      .join("\n");
    const cobertura = fireDiag.cobertura || {};
    const stops = fireDiag.stops_por_regime || {};
    fireSection = `${fireHeader}${fireRows}\n\n**Estratégia dominante por regime:**\n${estrategias || "N/D"}\n\n**Cobertura:** ${cobertura.ciclos_com_operacao ?? 0}/${cobertura.total_ciclos ?? 0} ciclos históricos com operação\n**Distribuição de stops:** ${JSON.stringify(stops)}`;
  }

  // Step 2b — Ranking por regime (TUNE v3.0)
  // Aceita tanto a estrutura crua do ativo {regime: {eleicao_status, ranking, ...}}
  // quanto a estrutura normalizada do step_2 {regimes: {...}, _meta, ...}
  let tuneRankingSection = "";
  if (tuneRanking && typeof tuneRanking === "object") {
    // Detecta estrutura normalizada (step_2.tune_ranking) vs crua (tune_ranking_estrategia)
    const regimesObj = tuneRanking.regimes
      ? tuneRanking.regimes
      : Object.fromEntries(Object.entries(tuneRanking).filter(([k]) => k !== "_meta"));
    const regimes = Object.entries(regimesObj);
    if (regimes.length > 0) {
      const rows = regimes.map(([regime, dados]) => {
        const status = fmt(dados.eleicao_status);
        const eleita = fmt(dados.estrategia_eleita);
        const n = fmt(dados.n_trades, "int");
        const ranking = (dados.ranking || []);
        const rankingStr = ranking
          .map((r) => `${fmt(r.estrategia)} IR=${fmt(r.ir, "float")} TP=${fmt(r.tp)} STOP=${fmt(r.stop)} (${fmt(r.trials, "int")} trials)`)
          .join(" / ");
        return `| ${regime} | ${status} | ${eleita} | ${n} | ${rankingStr || "—"} |`;
      }).join("\n");
      tuneRankingSection = `\n## Step 2b — Ranking por Regime (TUNE v3.0)\n| Regime | Status Eleição | Estratégia Eleita | N Trades | Candidatos (IR / TP / STOP) |\n|--------|---------------|-------------------|----------|------------------------------|\n${rows}\n`;
    }
  }

  return `${header}${step1Section}${step2Section}${tuneQualidadeSection}${tuneRankingSection}${gateSection}${gateDiagSection}${estrategiaSection}${fireSection}`;
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

function step1ModulesText(status, subModules) {
  if (status === "idle") return null;
  if (status === "done") return "TAPE ok | ORBIT ok | REFLECT ok";
  const tape = subModules?.TAPE;
  const orbit = subModules?.ORBIT;
  const reflect = subModules?.REFLECT;

  if (tape === "error") return "TAPE erro";
  if (orbit === "error") return "TAPE ok | ORBIT erro";
  if (reflect === "error") return "TAPE ok | ORBIT ok | REFLECT erro";
  if (reflect === "ok") return "TAPE ok | ORBIT ok | REFLECT ok";
  if (orbit === "ok") return "TAPE ok | ORBIT ok | REFLECT";
  if (tape === "ok") return "TAPE ok | ORBIT";
  return "TAPE";
}

function TuneRegimeProgressPanel({ progressByRegime }) {
  const rows = Object.entries(progressByRegime || {});
  if (!rows.length) return null;
  return (
    <div style={{ marginTop: 8, border: "1px solid var(--atlas-border)", background: "var(--atlas-surface)", borderRadius: 4, padding: 8 }}>
      <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-primary)", marginBottom: 6 }}>
        Eleição por regime (TUNE)
      </div>
      {rows.map(([regime, dados]) => {
        const status = dados?.eleicao_status || "in_progress";
        const ranking = dados?.ranking || [];
        const top = ranking[0] || null;
        const statusLabel = status === "competitiva"
          ? "competitiva"
          : status === "estrutural_fixo"
            ? "estrutural"
            : status === "bloqueado"
              ? "bloqueado"
              : "em andamento";
        return (
          <div key={regime} style={{ marginBottom: 6, padding: "6px 8px", border: "1px solid var(--atlas-border)", borderRadius: 3 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "monospace", fontSize: 9 }}>
              <span style={{ color: "var(--atlas-text-primary)", fontWeight: "bold" }}>{regime}</span>
              <span style={{ color: "var(--atlas-text-secondary)" }}>{statusLabel}</span>
            </div>
            {dados?.n_trades != null && (
              <div style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-text-secondary)", marginTop: 2 }}>
                N={dados.n_trades}
              </div>
            )}
            {status === "bloqueado" && (
              <div style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-text-secondary)", marginTop: 2 }}>
                ⚫ sem candidatos
              </div>
            )}
            {status === "estrutural_fixo" && dados?.estrategia_eleita && (
              <div style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-blue)", marginTop: 2 }}>
                {dados.estrategia_eleita}
              </div>
            )}
            {status === "competitiva" && dados?.estrategia_eleita && (
              <div style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-blue)", marginTop: 2 }}>
                {dados.estrategia_eleita}
              </div>
            )}
            {status === "in_progress" && top && (
              <div style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-blue)", marginTop: 2 }}>
                {top.estrategia} | IR {Number(top.ir || 0).toFixed(3)} | TP {top.tp != null ? Number(top.tp).toFixed(2) : "--"} | STOP {top.stop != null ? Number(top.stop).toFixed(2) : "--"}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
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
  const [gateError, setGateError] = useState(null);
  const [fireDiag, setFireDiag] = useState(null);
  const [gateCriteriosProgresso, setGateCriteriosProgresso] = useState([]);
  const [cotahistInfo, setCotahistInfo] = useState(null);
  const [showStep1Guard, setShowStep1Guard] = useState(false);
  const [subModules, setSubModules] = useState({ TAPE: null, ORBIT: null, REFLECT: null });
  const [tuneRanking, setTuneRanking] = useState(null);
  const [tunePendente, setTunePendente] = useState(false);
  const [tuneRankingConfirmado, setTuneRankingConfirmado] = useState(false);
  const [tuneRegimeProgress, setTuneRegimeProgress] = useState({});
  const [tuneEtapaLabel, setTuneEtapaLabel] = useState(null);

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
          if (step2Data?.trials_total != null) setTrialTotal(Number(step2Data.trials_total));

          const step3Payload = data?.step_3 || {};
          // Trata criterios=[] como ausente — normalize_gate_resultado retorna
          // objeto não-null mesmo quando gate_stored=null, o que causaria []
          // (truthy) a ganhar prioridade sobre gateCriteriosProgresso no render.
          const _gateRaw = step3Payload.gate_resultado;
          const gateResultadoInit = (_gateRaw?.criterios?.length > 0) ? _gateRaw : null;
          const fireDiagInit = step3Payload.fire_diagnostico || null;

          if (step3Data.status === "running") {
            if (gateResultadoInit && !fireDiagInit) {
              setStep3Fase(STEP3_FASES.FIRE);
            } else {
              // GATE está rodando (sem resultado ainda) ou estado ambíguo
              setStep3Fase(STEP3_FASES.GATE);
            }
          }

          if (gateResultadoInit) setGateResult(gateResultadoInit);
          if (fireDiagInit) setFireDiag(fireDiagInit);
          if (data?.steps?.["2_tune"]?.iniciado_em) setStep2IniciadoEm(new Date(data.steps["2_tune"].iniciado_em).getTime());
          if (data?.ultimo_evento_em) setUltimoEventoEm(new Date(data.ultimo_evento_em).getTime());

          // TUNE v3.0 ranking e banner tune_versao_pendente
          const step2Payload = data?.step_2 || {};
          if (step2Payload.tune_ranking) {
            setTuneRanking(step2Payload.tune_ranking);
            const jaConfirmados = !step2Payload.aguardando_confirmacao_regimes;
            setTuneRankingConfirmado(jaConfirmados);
            setTuneRegimeProgress(step2Payload.tune_ranking?.regimes || {});
          }
          // Banner pendência: buscar do ativo raw se step2 não trouxer
          try {
            const ativoRawRes = await fetch(`${API_BASE}/ativos/${ticker}`);
            if (ativoRawRes.ok) {
              const ativoRaw = await ativoRawRes.json();
              setTunePendente(Boolean(ativoRaw?.tune_versao_pendente));
            }
          } catch (_) { /* ignora */ }

      // Carregar TP/Stop persistido se step 2 já concluiu
      if (step2Data?.status === "done") {
        try {
          const ativoRes = await fetch(`${API_BASE}/ativos/${ticker}`);
          if (ativoRes.ok) {
            const ativoData = await ativoRes.json();
            if (ativoData?.take_profit != null) setBestTp(Number(ativoData.take_profit));
            if (ativoData?.stop_loss != null) setBestStop(Number(ativoData.stop_loss));
          }
        } catch (e) { /* ignora */ }
      }

      // Fallback: se step 3 está done mas não tem gateResult, buscar via endpoint
      const step3Status = step3Data?.status || persistedSteps["3_gate_fire"]?.status;
      if (step3Status === "done" && !gateResultadoInit) {
        try {
          const gateRes = await fetch(`${API_BASE}/ativos/${ticker}/gate-resultado`);
          if (gateRes.ok) setGateResult(await gateRes.json());
        } catch (e) { console.error("Erro gate-resultado:", e); }
      }
      // Fallback: se GATE aprovou mas não tem fireDiag, buscar via endpoint
      if (step3Status === "done" && gateResultadoInit?.resultado === "OPERAR" && !fireDiagInit) {
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

  // ──────────────────────────────────────────────────────────────────────────
  // Polling defensivo: reconcilia estado via API a cada 3s enquanto houver
  // step em "running". Protege contra eventos WS perdidos quando o drawer
  // desmonta/remonta (navegação) durante execução do GATE.
  //
  // Regras de merge:
  //   • Nunca regride status (done/error são terminais no frontend).
  //   • Só substitui gate_resultado se o backend tiver critérios ≥ ao local.
  //   • fire_diagnostico só é populado se ainda for null localmente.
  // Auto-desliga: o dep array inclui `steps`, então quando nenhum step está
  // running o effect re-executa e o cleanup limpa o interval.
  // ──────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    const anyRunning = Object.values(steps).some((s) => s?.status === "running");
    if (!anyRunning || !ticker) return undefined;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/delta-chaos/calibracao/${ticker}`);
        if (!res.ok) return;
        const data = await res.json();

        // Reconciliar steps (preserva running → done/error quando WS falhou).
        const serverSteps = data?.steps || {};
        setSteps((prev) => {
          const next = { ...prev };
          let changed = false;
          for (const key of Object.keys(next)) {
            const sv = serverSteps[key];
            if (!sv) continue;
            // Não regride estados terminais já observados no frontend.
            if (prev[key]?.status === "done" || prev[key]?.status === "error") continue;
            // Só avança se backend tem info diferente.
            if (
              sv.status !== prev[key]?.status ||
              sv.concluido_em !== prev[key]?.concluido_em ||
              sv.iniciado_em !== prev[key]?.iniciado_em
            ) {
              next[key] = { ...prev[key], ...sv };
              changed = true;
            }
          }
          return changed ? next : prev;
        });

        // Reconciliar gate_resultado (prefere backend se tiver lista maior).
        const gateApi = data?.step_3?.gate_resultado;
        if (gateApi?.criterios?.length > 0) {
          setGateResult((prev) => {
            const prevLen = prev?.criterios?.length || 0;
            return gateApi.criterios.length > prevLen ? gateApi : prev;
          });
          setGateCriteriosProgresso((prev) =>
            gateApi.criterios.length > prev.length ? gateApi.criterios : prev
          );
        }

        // Reconciliar fire_diagnostico (só popula se ainda não temos).
        const fireApi = data?.step_3?.fire_diagnostico;
        if (fireApi?.regimes?.length > 0) {
          setFireDiag((prev) => prev || fireApi);
        }
      } catch (_) {
        // ignora — próximo tick tenta de novo
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [steps, ticker]);

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
        setSubModules((prev) => ({ ...prev, [modulo]: "running" }));
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
        setTrialAtual(0);
        setTrialTotal(Number(steps?.["2_tune"]?.trials_total || 150));
        setBestIr(0);
        setBestTp(null);
        setBestStop(null);
        setSubModules({ TAPE: null, ORBIT: null, REFLECT: null });
        setTuneRegimeProgress({});
        setTuneEtapaLabel(null);
      }
      if (modulo === "GATE") {
        // Limpa dados de run anterior para evitar exibição fora de ordem
        setGateResult(null);
        setGateError(null);
        setFireDiag(null);
        setGateCriteriosProgresso([]);
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
        setSubModules((prev) => {
          const nextSub = { ...prev, [modulo]: ok ? "ok" : "error" };
          const allOk = ["TAPE", "ORBIT", "REFLECT"].every((m) => nextSub[m] === "ok");
          const anyError = ["TAPE", "ORBIT", "REFLECT"].some((m) => nextSub[m] === "error");
          setSteps((prevSteps) => ({
            ...prevSteps,
            "1_backtest_dados": {
              ...prevSteps["1_backtest_dados"],
              status: anyError ? "error" : allOk ? "done" : "running",
              concluido_em: allOk || anyError ? (evento?.data?.timestamp || new Date().toISOString()) : prevSteps["1_backtest_dados"]?.concluido_em,
              erro: anyError ? (evento?.data?.erro || "Erro em submódulo do step 1") : null,
            },
          }));
          return nextSub;
        });
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
        // Re-fetch ranking após TUNE completar para garantir run_id atualizado
        if (ok) {
          fetch(`${API_BASE}/delta-chaos/calibracao/${ticker}`)
            .then((r) => r.ok ? r.json() : null)
            .then((data) => {
              if (!data) return;
              const step2Payload = data?.step_2 || {};
              if (step2Payload.tune_ranking) {
                setTuneRanking(step2Payload.tune_ranking);
                setTuneRankingConfirmado(!step2Payload.aguardando_confirmacao_regimes);
                setTuneRegimeProgress(step2Payload.tune_ranking?.regimes || {});
              }
            })
            .catch(() => {});
        }
      }
      if (modulo === "GATE") {
        const ok = evento?.data?.status === "ok";
        const payloadGate = evento?.data?.gate_resultado || null;
        const temCriterios = Array.isArray(payloadGate?.criterios) && payloadGate.criterios.length > 0;

        if (payloadGate && temCriterios) {
          // Dados do evento são autoritativos — não chamar refreshGateResult()
          // que pode chegar antes do JSON ser gravado e sobrescrever com N/D
          setGateResult(payloadGate);
          // Espelho: se criterios vieram no payload final, atualiza o progressivo também.
          // Defende contra eventos dc_gate_criterion perdidos por WS reconectando.
          setGateCriteriosProgresso(payloadGate.criterios);
        } else if (ok) {
          // Payload ausente ou vazio — fallback para API (backend persiste em calibracao.gate_resultado)
          refreshGateResult();
        }

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
          setGateError(evento?.data?.erro || "erro desconhecido");
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
      }
      if (modulo === "FIRE") {
        const ok = evento?.data?.status === "ok";
        const payloadFire = evento?.data?.fire_diagnostico || null;
        if (payloadFire) {
          setFireDiag(payloadFire);
        } else if (ok) {
          // Evento sem fire_diagnostico — fallback para API
          refreshFireDiag();
        }
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
      }
    }

    if (evento?.type === "dc_gate_criterion") {
      const d = evento.data || {};
      if (d.id) {
        setGateCriteriosProgresso((prev) => {
          const idx = prev.findIndex((c) => c.id === d.id);
          if (idx >= 0) {
            const next = [...prev];
            next[idx] = d;
            return next;
          }
          return [...prev, d];
        });
      }
    }

    if (evento?.type === "dc_tune_progress") {
      const d = evento.data || {};
      if (d.trial != null) setTrialAtual(d.trial);
      if (d.total != null) setTrialTotal(d.total);
      if (d.ir != null) setBestIr(d.ir);
      if (d.best_tp != null) setBestTp(d.best_tp);
      if (d.best_stop != null) setBestStop(d.best_stop);
      if (d.etapa === "A" && d.regime) {
        const cand = d.candidato || "?";
        setTuneEtapaLabel(`Eleição ${d.regime}: ${cand} — ${d.trial ?? 0}/${d.total ?? 0}`);
      } else if (d.etapa === "B" && d.regime) {
        const strat = d.estrategia || d.candidato || "?";
        setTuneEtapaLabel(`${d.regime} — ${strat}: ${d.trial ?? 0}/${d.total ?? 0} trials | IR ${Number(d.ir || 0).toFixed(3)}`);
      }
    }

    if (evento?.type === "dc_tune_anomalia_detectada") {
      const d = evento.data || {};
      if (d.regime) {
        setTuneRegimeProgress((prev) => ({
          ...prev,
          [d.regime]: { ...(prev[d.regime] || {}), anomalia_detectada: true },
        }));
      }
    }

    if (evento?.type === "dc_tune_aplicacao_automatica") {
      const d = evento.data || {};
      if (d.regime) {
        setTuneRegimeProgress((prev) => ({
          ...prev,
          [d.regime]: { ...(prev[d.regime] || {}), aplicado_automaticamente: true },
        }));
      }
    }

    if (evento?.type === "dc_tune_anomalia_resolvida") {
      // Anomalia resolvida via resposta HTTP 200 do POST /tune/confirmar-regime-anomalia.
      // NÃO atualiza estado aqui — a fonte da verdade é a resposta do endpoint (handleAcao em RegimeRow).
      console.debug("[TUNE] dc_tune_anomalia_resolvida (diagnóstico):", evento?.data);
    }

    if (evento?.type === "dc_tune_eleicao_start") {
      const planejados = evento?.data?.regimes_planejados || [];
      const inicial = {};
      for (const regime of planejados) {
        inicial[regime] = {
          eleicao_status: "in_progress",
          confirmado: false,
          estrategia_eleita: null,
          ranking: [],
        };
      }
      setTuneRegimeProgress(inicial);
    }

    if (evento?.type === "dc_tune_eleicao_regime_start") {
      const d = evento?.data || {};
      if (!d.regime) return;
      const candidatos = d.candidatos ?? "?";
      setTuneEtapaLabel(`Eleição ${d.regime}: candidatos=${candidatos}`);
      setTuneRegimeProgress((prev) => ({
        ...prev,
        [d.regime]: {
          ...(prev[d.regime] || {}),
          eleicao_status: "in_progress",
          n_trades: d.n_trades,
          ranking: prev[d.regime]?.ranking || [],
          confirmado: prev[d.regime]?.confirmado || false,
          estrategia_eleita: prev[d.regime]?.estrategia_eleita || null,
        },
      }));
    }

    if (evento?.type === "dc_tune_eleicao_regime_complete") {
      const d = evento?.data || {};
      if (!d.regime) return;
      setTuneRegimeProgress((prev) => ({
        ...prev,
        [d.regime]: {
          ...(prev[d.regime] || {}),
          eleicao_status: d.eleicao_status || prev[d.regime]?.eleicao_status || "in_progress",
          n_trades: d.n_trades ?? prev[d.regime]?.n_trades,
          ranking: d.ranking || [],
          estrategia_eleita: d.estrategia_eleita ?? prev[d.regime]?.estrategia_eleita ?? null,
          ir_mediana: d.ir_mediana ?? null,
          confirmado: prev[d.regime]?.confirmado || false,
        },
      }));
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
    if (key === "2_tune" && proximoStep === key) return `Optuna ${trialTotal} trials · estimativa 4–8h`;
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
    const blocked = !gateResult || gateResult.resultado !== "OPERAR";
    const suffix = !gateResult ? "ERRO" : "BLOQUEADO";
    const filename = blocked
      ? `GATE_${ticker}_${cycle}_${now}_${suffix}.md`
      : `CALIBRACAO_${ticker}_${cycle}_${now}.md`;
    const markdown = buildMarkdownReport({
      ticker,
      cycle,
      steps,
      bestTp,
      bestStop,
      bestIr,
      gateResult,
      gateError,
      fireDiag: blocked ? null : fireDiag,
      tuneRanking,
    });
    downloadTextFile(filename, markdown);
  }

  async function handleExportarRelatorioBackend() {
    // Tenta enriquecer gate/fire via backend; sempre cai no fallback client-side se falhar
    try {
      const res = await fetch(`${API_BASE}/delta-chaos/calibracao/${ticker}/exportar-relatorio`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (res.ok) {
        const data = await res.json();
        if (data.status === "ok") {
          const now = new Date().toISOString().slice(0, 10);
          const enrichedGate = data.gate_resultado || gateResult;
          const cycle = enrichedGate?.ciclo || now.slice(0, 7);
          const blocked = !enrichedGate || enrichedGate.resultado !== "OPERAR";
          const suffix = !enrichedGate ? "ERRO" : "BLOQUEADO";
          const filename = blocked
            ? `GATE_${ticker}_${cycle}_${now}_${suffix}.md`
            : `CALIBRACAO_${ticker}_${cycle}_${now}.md`;
          downloadTextFile(
            filename,
            buildMarkdownReport({
              ticker,
              cycle,
              steps: data.steps || steps,
              bestTp,
              bestStop,
              bestIr,
              gateResult: enrichedGate,
              gateError,
              fireDiag: data.fire_diagnostico || fireDiag,
              tuneStats: data.tune_stats,
              gateStats: data.gate_stats,
              tuneRanking: data.tune_ranking_estrategia || tuneRanking,
            })
          );
          return;
        }
      }
    } catch (_) { /* ignora — cai no fallback */ }
    // Fallback: geração client-side com dados disponíveis no estado
    handleExport();
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

  const step3Done = steps["3_gate_fire"]?.status === "done";
  // Mostra o bloco "GATE BLOQUEADO" (botão Fechar) sempre que o step 3 terminou
  // e não estamos no fluxo OPERAR — cobre o edge case onde gateResult ficou
  // órfão (evento dc_module_complete perdido por WS reconectando).
  const gateBlocked = step3Done && gateResult?.resultado !== "OPERAR";
  const concluidoComFire = gateResult?.resultado === "OPERAR" && step3Done && fireDiag;

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
            {STEPS.find((s) => s.id === stepId)?.name || getStepLabel(stepId)}
          </div>
          {stepId === "1_backtest_dados" && (() => {
            const parts = step1ModulesText(status, subModules);
            if (!parts) return null;
            return (
              <div style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-blue)", marginTop: 2 }}>
                {parts}
              </div>
            );
          })()}
          {stepId === "2_tune" && status === "done" && (bestTp != null || bestStop != null) && (
            <div style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-blue)", marginTop: 2 }}>
              {`TP ${bestTp != null ? Number(bestTp).toFixed(2) : "--"} | STOP ${bestStop != null ? Number(bestStop).toFixed(2) : "--"}`}
            </div>
          )}
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
              {indexComplete && (
                <>
                  {tuneEtapaLabel ? (
                    <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-blue)", marginBottom: 4 }}>
                      {tuneEtapaLabel}
                    </div>
                  ) : (
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                      <span style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)" }}>
                        {trialAtual} / {trialTotal} trials
                      </span>
                      <span style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)" }}>
                        IR: {Number(bestIr || 0).toFixed(3)}
                      </span>
                    </div>
                  )}
                  <div style={{ width: "100%", height: 6, background: "var(--atlas-border)", borderRadius: 4, overflow: "hidden" }}>
                    <div style={{ width: `${trialTotal > 0 ? (trialAtual / trialTotal) * 100 : 0}%`, height: "100%", background: "var(--atlas-blue)" }} />
                  </div>
                  {(bestTp != null || bestStop != null) && (
                    <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-blue)", marginTop: 4 }}>
                      TP {bestTp != null ? Number(bestTp).toFixed(2) : "--"} | STOP {bestStop != null ? Number(bestStop).toFixed(2) : "--"}
                    </div>
                  )}
                </>
              )}
              <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-text-secondary)", marginTop: 4 }}>
                Tempo decorrido {elapsedForStep2()} (est. restante {estimatedForStep2()})
              </div>
              <TuneRegimeProgressPanel progressByRegime={tuneRegimeProgress} />
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

          {/* TUNE v3.1 — Ranking de eleição de estratégia (exibido após step 2 concluir; mostra placeholder se ranking ausente) */}
          {stepId === "2_tune" && status === "done" && (
            <TuneRankingPanel
              ticker={ticker}
              tuneRanking={tuneRanking}
              onTodosConfirmados={() => setTuneRankingConfirmado(true)}
            />
          )}

          {/* Step 3 aguardando confirmação de regimes (TUNE v3.0) */}
          {stepId === "3_gate_fire" && status === "paused" && (
            <div style={{ marginTop: 8 }}>
              {!tuneRankingConfirmado ? (
                <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-amber)" }}>
                  ⚠ Resolva as anomalias TUNE acima para liberar o step 3.
                </div>
              ) : (
                <button
                  onClick={handleRetomar}
                  style={{ marginTop: 4, padding: "4px 10px", background: "var(--atlas-green)", border: "none", color: "#fff", fontFamily: "monospace", fontSize: 9, borderRadius: 2, cursor: "pointer" }}
                >
                  Iniciar step 3 (GATE + FIRE)
                </button>
              )}
            </div>
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

              {/* GATE critérios — progressivos durante execução, definitivos após */}
              {(gateResult || gateError || gateCriteriosProgresso.length > 0) && (() => {
                // Render resiliente: prefere sempre a lista maior. Cobre o caso
                // onde gateResult veio com criterios parciais ou gateCriteriosProgresso
                // tem mais itens por ter acumulado eventos ao vivo.
                const criteriosEvent = gateResult?.criterios || [];
                const criterios = criteriosEvent.length >= gateCriteriosProgresso.length
                  ? criteriosEvent
                  : gateCriteriosProgresso;
                const emExecucao = !gateResult && !gateError && gateCriteriosProgresso.length > 0;
                const borderColor = gateResult
                  ? (gateResult.resultado === "OPERAR" ? "var(--atlas-green)" : "var(--atlas-red)")
                  : emExecucao ? "var(--atlas-blue)" : "var(--atlas-red)";
                return (
                  <div style={{ marginTop: 8, border: `1px solid ${borderColor}`, background: "var(--atlas-surface)", borderRadius: 4, padding: 8 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "monospace", fontSize: 10, color: "var(--atlas-text-primary)", marginBottom: 6 }}>
                      <span>GATE</span>
                      {emExecucao && (
                        <span style={{ color: "var(--atlas-blue)", fontSize: 9 }}>
                          {gateCriteriosProgresso.length}/8
                        </span>
                      )}
                    </div>
                    {gateError && !gateResult && (
                      <div style={{ fontFamily: "monospace", fontSize: 9, color: "var(--atlas-red)", marginBottom: 4 }}>
                        erro: {gateError}
                      </div>
                    )}
                    {criterios.map((c) => (
                      <div key={c.id} style={{ display: "flex", justifyContent: "space-between", fontFamily: "monospace", fontSize: 9, marginBottom: 2, color: c.passou ? "var(--atlas-green)" : "var(--atlas-red)" }}>
                        <span style={{ color: "var(--atlas-text-secondary)", marginRight: 6 }}>{c.id}</span>
                        <span style={{ flex: 1 }}>{c.nome || c.id}</span>
                        <span style={{ marginLeft: 8 }}>{c.passou ? "✓" : "✗"}{c.valor != null ? ` ${c.valor}` : " N/D"}</span>
                      </div>
                    ))}
                    {gateResult && (
                      <div style={{ marginTop: 6, paddingTop: 4, borderTop: "1px solid var(--atlas-border)", fontFamily: "monospace", fontSize: 10, color: gateResult.resultado === "OPERAR" ? "var(--atlas-green)" : "var(--atlas-red)", fontWeight: "bold" }}>
                        {gateResult.resultado === "OPERAR" ? "✓ OPERAR" : "✗ BLOQUEADO"}
                      </div>
                    )}
                  </div>
                );
              })()}

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
                <span>IR {r.ir?.toFixed(2)}{r.trades < 5 && <span style={{ fontFamily: "monospace", fontSize: 8, color: "var(--atlas-amber)", marginLeft: 4 }}>⚠ N&lt;5</span>}</span>
                <span style={{ color: r.worst_trade < 0 ? "var(--atlas-red)" : r.worst_trade > 0 ? "var(--atlas-green)" : "inherit" }}>{r.worst_trade != null ? `W: R$${Number(r.worst_trade).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "-"}</span>
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

        {/* Banner recalibração TUNE v3.0 obrigatória */}
        {tunePendente && (
          <div style={{ background: "rgba(245,158,11,0.15)", border: "1px solid var(--atlas-amber)", color: "var(--atlas-text-primary)", padding: "8px 12px", borderRadius: 4, marginBottom: 12, fontSize: 9, fontFamily: "monospace" }}>
            ⚠ Este ativo requer recalibração TUNE v3.0 — o FIRE está bloqueado para novas posições até a conclusão.
          </div>
        )}

        {/* Watchdog alert */}
        {watchdogAlert && (
          <div style={{ background: "rgba(245,158,11,0.2)", color: "var(--atlas-text-primary)", padding: "8px 12px", borderRadius: 4, marginBottom: 16, fontSize: 10, fontFamily: "monospace" }}>
            {watchdogAlert}
          </div>
        )}

        {/* Conclusão com FIRE — GATE aprovado */}
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

        {/* GATE bloqueado — só aviso + fechar */}
        {gateBlocked && (
          <div style={{ border: "1px solid var(--atlas-red)", background: "rgba(239,68,68,0.08)", padding: 12, marginBottom: 12, borderRadius: 4 }}>
            <div style={{ fontFamily: "monospace", fontSize: 12, color: "var(--atlas-red)", fontWeight: "bold", marginBottom: 8 }}>
              ✗ GATE BLOQUEADO — {ticker}
            </div>
            <div style={{ fontFamily: "monospace", fontSize: 10, color: "var(--atlas-text-secondary)", marginBottom: 10 }}>
              Critério(s) reprovado(s): {(gateResult?.falhas || []).join(", ") || "N/D"}
            </div>
            <button
              onClick={onClose}
              style={{ width: "100%", padding: "6px 10px", background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", color: "var(--atlas-text-secondary)", fontFamily: "monospace", fontSize: 10, borderRadius: 2, cursor: "pointer" }}
            >
              Fechar
            </button>
          </div>
        )}

        {/* Cards de steps */}
        <div style={{ background: "var(--atlas-bg)", padding: 12, borderRadius: 4, marginBottom: 12 }}>
          {STEPS.map((step) => renderStepCard(step.id))}
        </div>

        {/* Botão exportar relatório — sempre visível, habilitado quando step 3 concluiu */}
        {(() => {
          const s3Status = steps["3_gate_fire"]?.status;
          const relatorioDisponivel = (s3Status === "done" || s3Status === "error") && (gateResult || gateError);
          return (
            <button
              onClick={relatorioDisponivel ? handleExportarRelatorioBackend : undefined}
              disabled={!relatorioDisponivel}
              style={{
                width: "100%",
                padding: "7px 10px",
                background: relatorioDisponivel ? "transparent" : "transparent",
                border: `1px solid ${relatorioDisponivel ? "var(--atlas-blue)" : "var(--atlas-border)"}`,
                color: relatorioDisponivel ? "var(--atlas-blue)" : "var(--atlas-text-secondary)",
                fontFamily: "monospace",
                fontSize: 9,
                borderRadius: 2,
                cursor: relatorioDisponivel ? "pointer" : "default",
                letterSpacing: "0.06em",
                textTransform: "uppercase",
                opacity: relatorioDisponivel ? 1 : 0.45,
                marginBottom: 8,
              }}
              onMouseEnter={relatorioDisponivel ? (e) => { e.currentTarget.style.background = "rgba(59,130,246,0.1)"; } : undefined}
              onMouseLeave={relatorioDisponivel ? (e) => { e.currentTarget.style.background = "transparent"; } : undefined}
            >
              ↓ Exportar relatório .md
            </button>
          );
        })()}

      </div>
      <style>{PULSE_ANIMATION}</style>
    </>
  );
}


