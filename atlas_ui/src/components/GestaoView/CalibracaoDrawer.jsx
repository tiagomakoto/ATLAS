import React, { useState, useEffect } from "react";
import useWebSocket from "../../hooks/useWebSocket";

const API_BASE = "http://localhost:8000";

export default function CalibracaoDrawer({ ticker, onClose }) {
  const [calibracao, setCalibracao] = useState(null);
  const [watchdogAlert, setWatchdogAlert] = useState(null);
  const [trialAtual, setTrialAtual] = useState(0);
  const [trialTotal, setTrialTotal] = useState(0);
  const [bestIr, setBestIr] = useState(0);
  const [ultimoEventoEm, setUltimoEventoEm] = useState(0);
  const [step2IniciadoEm, setStep2IniciadoEm] = useState(0);
  const [steps, setSteps] = useState({
    "1_backtest_dados": { status: "idle", iniciado_em: null, concluido_em: null },
    "2_tune": { status: "idle", iniciado_em: null, concluido_em: null },
    "3_backtest_gate": { status: "idle", iniciado_em: null, concluido_em: null }
  });

  // Novos estados para rastrear progresso da indexação de dias
  const [indexProgress, setIndexProgress] = useState({ current: 0, total: 0 });
  const [showIndexProgress, setShowIndexProgress] = useState(false);
  const [indexComplete, setIndexComplete] = useState(false);

  // Estado para rastrear a fase atual da calibração
  const [faseCalibracao, setFaseCalibracao] = useState("integridade");

// Estado para rastrear sub-módulos do step 1 (TAPE, ORBIT, REFLECT)
const [subModules, setSubModules] = useState({
  "TAPE": null,
  "ORBIT": null,
  "REFLECT": null
});

// Estado para armazenar valores de parametrização (TP/STOP)
const [parametros, setParametros] = useState({ take_profit: null, stop_loss: null });

  // Carregar estado inicial da calibração
  useEffect(() => {
    const fetchOnboarding = async () => {
      try {
        const res = await fetch(`${API_BASE}/delta-chaos/calibracao/${ticker}`);
        if (res.ok) {
          const data = await res.json();
          setCalibracao(data);
          // Inicializar steps com base no estado carregado
          if (data?.steps) {
            setSteps({
              "1_backtest_dados": {
                status: data.steps["1_backtest_dados"]?.status || "idle",
                iniciado_em: data.steps["1_backtest_dados"]?.iniciado_em || null,
                concluido_em: data.steps["1_backtest_dados"]?.concluido_em || null
              },
              "2_tune": {
                status: data.steps["2_tune"]?.status || "idle",
                iniciado_em: data.steps["2_tune"]?.iniciado_em || null,
                concluido_em: data.steps["2_tune"]?.concluido_em || null
              },
              "3_backtest_gate": {
                status: data.steps["3_backtest_gate"]?.status || "idle",
                iniciado_em: data.steps["3_backtest_gate"]?.iniciado_em || null,
                concluido_em: data.steps["3_backtest_gate"]?.concluido_em || null
              }
            });
          }
          // Inicializar métricas de TUNE se disponíveis
          if (data.steps?.["2_tune"]?.trials_completos) {
            setTrialAtual(data.steps["2_tune"].trials_completos);
          }
          if (data.steps?.["2_tune"]?.trials_total) {
            setTrialTotal(data.steps["2_tune"].trials_total);
          }
          if (data.steps?.["2_tune"]?.best_ir) {
            setBestIr(data.steps["2_tune"].best_ir);
          }
          if (data.ultimo_evento_em) {
            setUltimoEventoEm(new Date(data.ultimo_evento_em).getTime());
          }
          if (data.steps?.["2_tune"]?.iniciado_em) {
            setStep2IniciadoEm(new Date(data.steps["2_tune"].iniciado_em).getTime());
          }
        }
      } catch (error) {
        console.error("Erro ao carregar calibração:", error);
      }
    };

    if (ticker) {
      fetchOnboarding();
    }
  }, [ticker]);

  // Watchdog: alerta se sem sinal por 5 minutos
  useEffect(() => {
    if (!ultimoEventoEm || !step2IniciadoEm) return;

    const interval = setInterval(() => {
      const now = Date.now();
      const minutesSinceLastEvent = Math.floor((now - ultimoEventoEm) / 60000);

      if (steps["2_tune"].status === "running" && minutesSinceLastEvent >= 5 && !watchdogAlert) {
        setWatchdogAlert(`⚠ Sem sinal há ${minutesSinceLastEvent}min — processo pode ter sido interrompido`);
      } else if (steps["2_tune"].status === "running" && minutesSinceLastEvent < 5 && watchdogAlert) {
        setWatchdogAlert(null);
      }
    }, 60000); // Verifica a cada minuto

return () => clearInterval(interval);
}, [ultimoEventoEm, step2IniciadoEm, steps["2_tune"].status, watchdogAlert]);

// Buscar TP/STOP do ativo quando GATE concluído
useEffect(() => {
  if (getStepStatus("3_backtest_gate") === "done") {
    const fetchParametros = async () => {
      try {
        const res = await fetch(`${API_BASE}/ativos/${ticker}`);
        if (res.ok) {
          const data = await res.json();
          setParametros({
            take_profit: data.take_profit,
            stop_loss: data.stop_loss
          });
        }
      } catch (error) {
        console.error("Erro ao buscar parâmetros:", error);
      }
    };
    fetchParametros();
  }
}, [ticker, steps]);

// Conexão WebSocket para eventos em tempo real
  const wsUrl = `ws://${window.location.hostname}:${window.location.port || '8000'}/ws/events`;
  useWebSocket(wsUrl, (evento) => {
    handleEvento(evento);
  });

  const handleEvento = (evento) => {
    console.log("[CALIBRACAO] Evento recebido:", evento.type, evento.data);

    const stepMap = {
      "ORBIT": "1_backtest_dados",
      "TUNE": "2_tune",
      "GATE": "3_backtest_gate"
    };

    // Mapear sub-módulos do step 1 (TAPE, ORBIT, REFLECT)
    const subModuleMap = {
      "TAPE": "1_backtest_dados",
      "ORBIT": "1_backtest_dados",
      "REFLECT": "1_backtest_dados"
    };

    if (evento.type === "dc_module_start") {
      const modulo = evento.data?.modulo;
      const stepKey = stepMap[modulo];

      // Atualizar sub-módulos do step 1
      if (subModuleMap[modulo] === "1_backtest_dados") {
        setSubModules(prev => ({ ...prev, [modulo]: "running" }));
        // Quando qualquer módulo do step 1 inicia, setar fase como integridade
        setFaseCalibracao("integridade");
      }

      if (stepKey) {
        setSteps(prev => ({
          ...prev,
          [stepKey]: {
            ...prev[stepKey],
            status: "running",
            iniciado_em: evento.data?.timestamp || new Date().toISOString()
          }
        }));
        if (stepKey === "2_tune") {
          setStep2IniciadoEm(new Date().getTime());
          // Resetar progresso de indexação quando step 2 inicia
          setIndexProgress({ current: 0, total: 0 });
          setShowIndexProgress(false);
          setIndexComplete(false);
          // Quando step 2 inicia, resetar fase para integridade (ainda não começou a indexação)
          setFaseCalibracao("integridade");
        }
      }
    }

if (evento.type === "dc_module_complete") {
    const modulo = evento.data?.modulo;
    const status = evento.data?.status;
    const stepKey = stepMap[modulo];

    // Atualizar sub-módulos do step 1
    if (subModuleMap[modulo] === "1_backtest_dados") {
        setSubModules(prev => ({ ...prev, [modulo]: status === "ok" ? "ok" : "error" }));
    }

    if (stepKey) {
        setSteps(prev => ({
            ...prev,
            [stepKey]: {
                ...prev[stepKey],
                status: status === "ok" ? "done" : "error",
                concluido_em: evento.data?.timestamp || new Date().toISOString()
            }
        }));
    }
    
    // Mostrar mensagem de erro para TUNE
    if (modulo === "TUNE" && status === "error") {
        const erro = evento.data?.erro || "Erro desconhecido";
        setWatchdogAlert(`✗ TUNE falhou: ${erro}`);
    }
}

if (evento.type === "dc_tune_progress") {
    const d = evento.data;
    console.log("[CALIBRACAO] dc_tune_progress:", d); // Debug para verificar se eventos estão chegando
    if (d?.trial !== undefined) setTrialAtual(d.trial);
    if (d?.total !== undefined) setTrialTotal(d.total);
    if (d?.ir !== undefined) setBestIr(d.ir);
    setUltimoEventoEm(Date.now());
  }

  // IPC: eventos de indexação via JSONL
  if (evento.type === "dc_tune_index_start") {
    const d = evento.data;
    console.log("[CALIBRACAO] dc_tune_index_start:", d);
    setIndexProgress({ current: 0, total: d?.total || 0 });
    setShowIndexProgress(true);
    setIndexComplete(false);
    setFaseCalibracao("indexacao");
    setUltimoEventoEm(Date.now());
  }

  if (evento.type === "dc_tune_index_progress") {
    const d = evento.data;
    console.log("[CALIBRACAO] dc_tune_index_progress:", d);
    setIndexProgress({ current: d?.current || 0, total: d?.total || 0 });
    setShowIndexProgress(true);
    setIndexComplete(false);
    setFaseCalibracao("indexacao");
    setUltimoEventoEm(Date.now());
  }

  if (evento.type === "dc_tune_index_complete") {
    const d = evento.data;
    console.log("[CALIBRACAO] dc_tune_index_complete:", d);
    setIndexComplete(true);
    setShowIndexProgress(false);
    setFaseCalibracao("otimizacao");
    setUltimoEventoEm(Date.now());
  }

  // Legado: Tratar logs de progresso da indexação de dias (DEPRECADO - usar IPC acima)
    if (evento.type === "terminal_log") {
      const message = evento.data?.message;
      if (!message) return;

      // Detectar progresso de indexação: "TUNE [TICKER] indexando dias: X/Y (Z%)"
      // Regex ajustado para capturar números com vírgulas (ex: 1,000/6,004)
      const indexRegex = /TUNE \[([A-Z0-9]+)\] indexando dias: ([\d,]+)\/([\d,]+)/;
      const match = message.match(indexRegex);
if (match) {
    // Remover vírgulas antes de converter para int
    const current = parseInt(match[2].replace(/,/g, ''));
    const total = parseInt(match[3].replace(/,/g, ''));
    setIndexProgress({ current, total });
    setShowIndexProgress(true);
    setIndexComplete(false);
    setFaseCalibracao("indexacao");
    setUltimoEventoEm(Date.now());
    return;
  }

  // Detectar conclusão da indexação: "pré-cômputo concluído"
  if (message.includes("pré-cômputo concluído")) {
    setIndexComplete(true);
    setFaseCalibracao("otimizacao");
    setUltimoEventoEm(Date.now());
    return;
  }
    }
  };

  const getStepStatus = (stepKey) => {
    return steps[stepKey]?.status || "idle";
  };

  const getStepName = (stepKey) => {
    const names = {
      "1_backtest_dados": "Integridade de dados",
      "2_tune": "Parametrização",
      "3_backtest_gate": "GATE"
    };
    return names[stepKey] || stepKey;
  };

  const getProximoStep = () => {
    const stepKeys = ["1_backtest_dados", "2_tune", "3_backtest_gate"];
    let ultimoDone = -1;
    for (let i = 0; i < stepKeys.length; i++) {
      if (getStepStatus(stepKeys[i]) === "done") {
        ultimoDone = i;
      }
    }
    // O próximo é o primeiro idle após o último done
    for (let i = ultimoDone + 1; i < stepKeys.length; i++) {
      if (getStepStatus(stepKeys[i]) === "idle") {
        return stepKeys[i];
      }
    }
    return null; // Todos done ou running
  };

  const getStepLabel = (stepKey) => {
    const status = getStepStatus(stepKey);
    const proximoStep = getProximoStep();
    if (status === "idle" && stepKey === proximoStep) {
      return "PRÓXIMO";
    }
    const labels = {
      idle: "PENDENTE",
      running: "EXECUTANDO",
      done: "CONCLUÍDO",
      error: "ERRO",
      paused: "PAUSADO"
    };
    return labels[status] || "PENDENTE";
  };

  const getStepIcon = (stepKey) => {
    const status = getStepStatus(stepKey);
    const icons = {
      idle: "○",
      running: "⟳",
      done: "●",
      error: "✗",
      paused: "⏸"
    };
    return icons[status] || "○";
  };

  const getStepColor = (stepKey) => {
    const status = getStepStatus(stepKey);
    const colors = {
      idle: "var(--atlas-text-secondary)",
      running: "var(--atlas-blue)",
      done: "var(--atlas-green)",
      error: "var(--atlas-red)",
      paused: "var(--atlas-amber)"
    };
    return colors[status] || "var(--atlas-text-secondary)";
  };

  const getStepColorBg = (stepKey) => {
    const status = getStepStatus(stepKey);
    const proximoStep = getProximoStep();

    // Mimetizar OrchestratorLogDrawer: rodando = fundo azul
    if (status === "running") {
      return "rgba(59,130,246,0.15)";
    }

    // Próximo step tem destaque azul sutil
    if (status === "idle" && stepKey === proximoStep) {
      return "rgba(59,130,246,0.08)";
    }

    const colors = {
      idle: "transparent",
      done: "rgba(34,197,94,0.1)",
      error: "rgba(239,68,68,0.1)",
      paused: "rgba(245,158,11,0.1)"
    };
    return colors[status] || "transparent";
  };

  const getStepBorderColor = (stepKey) => {
    const status = getStepStatus(stepKey);
    const proximoStep = getProximoStep();

    // Mimetizar OrchestratorLogDrawer: rodando = borda azul
    if (status === "running") {
      return "var(--atlas-blue)";
    }

    // Próximo step tem borda azul sutil
    if (status === "idle" && stepKey === proximoStep) {
      return "rgba(59,130,246,0.3)";
    }

    const colors = {
      idle: "transparent",
      done: "var(--atlas-green)",
      error: "var(--atlas-red)",
      paused: "var(--atlas-amber)"
    };
    return colors[status] || "transparent";
  };

  const getStepOpacity = (stepKey) => {
    const status = getStepStatus(stepKey);
    const proximoStep = getProximoStep();

    // Mimetizar OrchestratorLogDrawer: espera = opacidade 0.5
    if (status === "idle" && stepKey !== proximoStep) {
      return 0.5;
    }
    return 1;
  };

  const calculateDuration = (stepKey) => {
    const step = steps[stepKey];
    if (!step?.iniciado_em || !step?.concluido_em) return null;

    const start = new Date(step.iniciado_em);
    const end = new Date(step.concluido_em);
    const diffMs = end - start;

    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diffMs % (1000 * 60)) / 1000);

    if (hours > 0) return `${hours}h ${minutes}m ${seconds}s`;
    if (minutes > 0) return `${minutes}m ${seconds}s`;
    return `${seconds}s`;
  };

  const getStepDescription = (stepKey) => {
    const status = getStepStatus(stepKey);
    const proximoStep = getProximoStep();

    // Descrição prévia para TUNE quando é o próximo (sem estimativa)
    if (status === "idle" && stepKey === "2_tune" && stepKey === proximoStep) {
      return "Optuna 200 trials";
    }

    const descriptions = {
      idle: "Aguardando início",
      running: "Em execução",
      done: "Concluído",
      error: "Falhou",
      paused: "Pausado"
    };
    return descriptions[status] || "Aguardando início";
  };

  // Função para exibir sub-módulos do step 1 (TAPE, ORBIT, REFLECT)
  const getSubModulesDisplay = (stepKey) => {
    if (stepKey !== "1_backtest_dados") return null;
    const modules = ["TAPE", "ORBIT", "REFLECT"];
    const parts = [];
    for (const mod of modules) {
      const status = subModules[mod];
      if (status === null) continue;
      if (status === "running") {
        parts.push(mod);
      } else if (status === "ok") {
        parts.push(`${mod} ok`);
      } else if (status === "error") {
        parts.push(`${mod} erro`);
      }
    }
    return parts.length > 0 ? parts.join(" | ") : null;
  };

  const getStepTime = (stepKey) => {
    const status = getStepStatus(stepKey);
    if (status === "done" && steps[stepKey]?.concluido_em) {
      const timestamp = new Date(steps[stepKey].concluido_em).toLocaleString("pt-BR");
      const duration = calculateDuration(stepKey);
      if (duration) {
        return `${timestamp} · duração: ${duration}`;
      }
      return timestamp;
    }
    return "";
  };

  const handleRetomar = async () => {
    try {
      const res = await fetch(`${API_BASE}/delta-chaos/calibracao/${ticker}/retomar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      if (!res.ok) {
        // Apenas em caso de erro, atualizar estado
        setSteps(prev => ({
          ...prev,
          "2_tune": {
            ...prev["2_tune"],
            status: "error"
          }
        }));
        console.error("Erro ao retomar calibração:", res.statusText);
      }
      // Em caso de sucesso, NÃO atualizar - aguardar evento WebSocket
    } catch (error) {
      console.error("Erro ao retomar:", error);
      setSteps(prev => ({
        ...prev,
        "2_tune": {
          ...prev["2_tune"],
          status: "error"
        }
      }));
    }
  };

  const handleIniciar = async () => {
    // Feedback imediato: atualizar estado para "EXECUTANDO" antes mesmo do fetch
    const agora = new Date().toISOString();
    setSteps(prev => ({
      ...prev,
      "1_backtest_dados": {
        ...prev["1_backtest_dados"],
        status: "running",
        iniciado_em: agora
      }
    }));
    setStep2IniciadoEm(new Date().getTime());

    // Resetar sub-módulos do step 1
    setSubModules({
      "TAPE": null,
      "ORBIT": null,
      "REFLECT": null
    });

    try {
      const res = await fetch(`${API_BASE}/delta-chaos/calibracao/iniciar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker, confirm: true, description: "Iniciar calibração" })
      });
      if (!res.ok) {
        // Apenas em caso de erro, atualizar estado para error
        setSteps(prev => ({
          ...prev,
          "1_backtest_dados": {
            ...prev["1_backtest_dados"],
            status: "error"
          }
        }));
        console.error("Erro ao iniciar calibração:", res.statusText);
      }
      // Em caso de sucesso, NÃO atualizar - aguardar evento WebSocket para confirmar
    } catch (error) {
      console.error("Erro ao iniciar:", error);
      setSteps(prev => ({
        ...prev,
        "1_backtest_dados": {
          ...prev["1_backtest_dados"],
          status: "error"
        }
      }));
    }
  };

  const calculateElapsedTime = (iniciado_em) => {
    if (!iniciado_em) return "0s";
    const start = new Date(iniciado_em);
    const now = new Date();
    const diff = now - start;
    const seconds = Math.floor(diff / 1000) % 60;
    const minutes = Math.floor(diff / (1000 * 60)) % 60;
    const hours = Math.floor(diff / (1000 * 60 * 60));

    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${seconds}s`;
    return `${seconds}s`;
  };

  const calculateAverageTime = (iniciado_em, trials_completos) => {
    if (!iniciado_em || trials_completos <= 0) return "0s";
    const start = new Date(iniciado_em);
    const now = new Date();
    const diff = now - start;
    const avgMs = diff / trials_completos;
    const seconds = Math.floor(avgMs / 1000);

    return `${seconds}s`;
  };

  const calculateEstimatedTime = (iniciado_em, trials_completos, trials_total) => {
    if (!iniciado_em || trials_completos <= 0) return "0s";
    const start = new Date(iniciado_em);
    const now = new Date();
    const diff = now - start;
    const avgMs = diff / trials_completos;
    const remainingTrials = trials_total - trials_completos;
    const remainingMs = remainingTrials * avgMs;

    const seconds = Math.floor(remainingMs / 1000) % 60;
    const minutes = Math.floor(remainingMs / (1000 * 60)) % 60;
    const hours = Math.floor(remainingMs / (1000 * 60 * 60));

    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${seconds}s`;
    return `${seconds}s`;
  };

  // TAREFA 5: Implementar botões de conclusão
  const handleConfirmarOperar = async () => {
    try {
      const res = await fetch(`${API_BASE}/ativos/${ticker}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "OPERAR" })
      });
      if (res.ok) {
        onClose();
      }
    } catch (error) {
      console.error("Erro ao confirmar OPERAR:", error);
    }
  };

  // Não bloquear renderização — WebSocket precisa montar independente do fetch
  // if (!calibracao) return null;

  return (
    <><div style={{
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
      boxShadow: "-5px 0 15px rgba(0,0,0,0.1)"
    }}>
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: 16
      }}>
        <h3 style={{ margin: 0, fontFamily: "monospace", fontSize: 14, color: "var(--atlas-text-primary)" }}>
          CALIBRAÇÃO — {ticker}
        </h3>
        <button
          onClick={onClose}
          style={{
            background: "transparent",
            border: "none",
            fontSize: 16,
            color: "var(--atlas-text-secondary)",
            cursor: "pointer"
          }}
        >
          ×
        </button>
      </div>

      {watchdogAlert && (
        <div style={{
          background: "var(--atlas-amber)",
          color: "var(--atlas-text-primary)",
          padding: "8px 12px",
          borderRadius: 4,
          marginBottom: 16,
          fontSize: 10,
          fontFamily: "monospace"
        }}>
          {watchdogAlert}
        </div>
      )}



      <div style={{
        background: "var(--atlas-bg)",
        padding: 12,
        borderRadius: 4,
        marginBottom: 16
      }}>
        <div style={{
          display: "flex",
          alignItems: "center",
          marginBottom: 8,
          padding: "8px 12px",
          background: getStepColorBg("1_backtest_dados"),
          border: `1px solid ${getStepBorderColor("1_backtest_dados")}`,
          borderRadius: 2,
          opacity: getStepOpacity("1_backtest_dados")
        }}>
          <span style={{
            fontSize: 14,
            color: getStepColor("1_backtest_dados"),
            fontWeight: "bold",
            marginRight: 8,
            animation: (getStepStatus("1_backtest_dados") === "running" || (getStepStatus("1_backtest_dados") === "idle" && "1_backtest_dados" === getProximoStep())) ? "pulse 1s infinite" : "none"
          }}>
            {getStepIcon("1_backtest_dados")}
          </span>
          <div>
            <div style={{
              fontFamily: "monospace",
              fontSize: 11,
              color: getStepColor("1_backtest_dados"),
              fontWeight: "bold"
            }}>
              {getStepLabel("1_backtest_dados")}
            </div>
            <div style={{
              fontFamily: "monospace",
              fontSize: 9,
              color: "var(--atlas-text-secondary)"
            }}>
              {getStepName("1_backtest_dados")}
            </div>
            {getSubModulesDisplay("1_backtest_dados") && (
              <div style={{
                fontFamily: "monospace",
                fontSize: 8,
                color: "var(--atlas-blue)",
                marginTop: 2
              }}>
                {getSubModulesDisplay("1_backtest_dados")}
              </div>
            )}
            <div style={{
              fontFamily: "monospace",
              fontSize: 9,
              color: "var(--atlas-text-secondary)"
            }}>
              {getStepDescription("1_backtest_dados")}
              {getStepTime("1_backtest_dados") && (
                <span style={{ marginLeft: 8 }}>
                  {getStepTime("1_backtest_dados")}
                </span>
              )}
            </div>
          </div>
        </div>

        <div style={{
          display: "flex",
          alignItems: "center",
          marginBottom: 8,
          padding: "8px 12px",
          background: getStepColorBg("2_tune"),
          border: `1px solid ${getStepBorderColor("2_tune")}`,
          borderRadius: 2,
          opacity: getStepOpacity("2_tune")
        }}>
          <span style={{
            fontSize: 14,
            color: getStepColor("2_tune"),
            fontWeight: "bold",
            marginRight: 8,
            animation: (getStepStatus("2_tune") === "running" || (getStepStatus("2_tune") === "idle" && "2_tune" === getProximoStep())) ? "pulse 1s infinite" : "none"
          }}>
            {getStepIcon("2_tune")}
          </span>
          <div>
            <div style={{
              fontFamily: "monospace",
              fontSize: 11,
              color: getStepColor("2_tune"),
              fontWeight: "bold"
            }}>
              {getStepLabel("2_tune")}
            </div>
            <div style={{
              fontFamily: "monospace",
              fontSize: 9,
              color: "var(--atlas-text-secondary)"
            }}>
              {getStepName("2_tune")}
            </div>
            <div style={{
              fontFamily: "monospace",
              fontSize: 9,
              color: "var(--atlas-text-secondary)"
            }}>
              {getStepDescription("2_tune")}
              {getStepTime("2_tune") && (
                <span style={{ marginLeft: 8 }}>
                  {getStepTime("2_tune")}
                </span>
              )}
            </div>

            {getStepStatus("2_tune") === "running" && (
              <>
                <div style={{
                  marginTop: 8,
                  padding: "8px 12px",
                  background: "var(--atlas-surface)",
                  borderRadius: 4,
                  border: "1px solid var(--atlas-border)"
                }}>

                  {/* Barra de progresso da indexação de dias */}
                  {showIndexProgress && !indexComplete && (
                    <div style={{
                      marginBottom: 12,
                      padding: "8px 12px",
                      background: "var(--atlas-surface)",
                      borderRadius: 4,
                      border: "1px solid var(--atlas-border)"
                    }}>
                      <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        marginBottom: 4
                      }}>
                        <span style={{
                          fontFamily: "monospace",
                          fontSize: 9,
                          color: "var(--atlas-text-secondary)"
                        }}>
                          Indexando dias: {indexProgress.current} / {indexProgress.total}
                        </span>
                        <span style={{
                          fontFamily: "monospace",
                          fontSize: 9,
                          color: "var(--atlas-text-secondary)"
                        }}>
                          {Math.round((indexProgress.current / indexProgress.total) * 100)}%
                        </span>
                      </div>
                      <div style={{
                        width: "100%",
                        height: 8,
                        background: "var(--atlas-border)",
                        borderRadius: 4,
                        overflow: "hidden"
                      }}>
                        <div style={{
                          height: "100%",
                          background: "var(--atlas-blue)",
                          width: `${(indexProgress.current / indexProgress.total) * 100}%`
                        }} />
                      </div>
                    </div>
                  )}

                  {/* Texto de conclusão da indexação */}
                  {indexComplete && (
                    <div style={{
                      marginBottom: 12,
                      padding: "8px 12px",
                      background: "var(--atlas-surface)",
                      borderRadius: 4,
                      border: "1px solid var(--atlas-border)"
                    }}>
                      <span style={{
                        fontFamily: "monospace",
                        fontSize: 9,
                        color: "var(--atlas-green)"
                      }}>
                        {indexProgress.total} dias indexados
                      </span>
                    </div>
                  )}

{/* Barra de progresso dos trials */}
{steps["2_tune"].status === "running" && (
                    <div style={{
                      marginBottom: 12,
                      padding: "8px 12px",
                      background: "var(--atlas-surface)",
                      borderRadius: 4,
                      border: "1px solid var(--atlas-border)"
                    }}>
                      <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        marginBottom: 4
                      }}>
                        <span style={{
                          fontFamily: "monospace",
                          fontSize: 9,
                          color: "var(--atlas-text-secondary)"
                        }}>
                          {trialAtual} / {trialTotal} trials
                        </span>
                        <span style={{
                          fontFamily: "monospace",
                          fontSize: 9,
                          color: "var(--atlas-text-secondary)"
                        }}>
                          IR: {bestIr.toFixed(3) || "0.000"}
                        </span>
                      </div>
                      <div style={{
                        width: "100%",
                        height: 8,
                        background: "var(--atlas-border)",
                        borderRadius: 4,
                        overflow: "hidden"
                      }}>
                        <div style={{
                          height: "100%",
                          background: "var(--atlas-blue)",
                          width: `${trialTotal > 0 ? (trialAtual / trialTotal * 100) : 0}%`
                        }} />
                      </div>
                    </div>
                  )}
                </div>

                {/* Tempo decorrido e estimativas - agora fora da caixa preta */}
                <div style={{
                  marginTop: 8,
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: 9,
                  fontFamily: "monospace",
                  color: "var(--atlas-text-secondary)"
                }}>
                  <span>
                    Tempo decorrido: {calculateElapsedTime(step2IniciadoEm)}
                  </span>
                  <span>
                    Estimativa restante: {calculateEstimatedTime(step2IniciadoEm, trialAtual, trialTotal)}
                  </span>
                </div>

                <div style={{
                  marginTop: 4,
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: 9,
                  fontFamily: "monospace",
                  color: "var(--atlas-text-secondary)"
                }}>
                  <span>
                    Tempo médio/trial: {calculateAverageTime(step2IniciadoEm, trialAtual)}
                  </span>
                </div>
              </>
            )}

            {getStepStatus("2_tune") === "paused" && (
              <button
                onClick={handleRetomar}
                style={{
                  marginTop: 8,
                  padding: "4px 10px",
                  background: "var(--atlas-blue)",
                  border: "none",
                  color: "#fff",
                  fontFamily: "monospace",
                  fontSize: 9,
                  borderRadius: 2,
                  cursor: "pointer"
                }}
              >
                Retomar
              </button>
            )}
          </div>
        </div>

        <div style={{
          display: "flex",
          alignItems: "center",
          marginBottom: 8,
          padding: "8px 12px",
          background: getStepColorBg("3_backtest_gate"),
          border: `1px solid ${getStepBorderColor("3_backtest_gate")}`,
          borderRadius: 2,
          opacity: getStepOpacity("3_backtest_gate")
        }}>
          <span style={{
            fontSize: 14,
            color: getStepColor("3_backtest_gate"),
            fontWeight: "bold",
            marginRight: 8,
            animation: (getStepStatus("3_backtest_gate") === "running" || (getStepStatus("3_backtest_gate") === "idle" && "3_backtest_gate" === getProximoStep())) ? "pulse 1s infinite" : "none"
          }}>
            {getStepIcon("3_backtest_gate")}
          </span>
          <div>
            <div style={{
              fontFamily: "monospace",
              fontSize: 11,
              color: getStepColor("3_backtest_gate"),
              fontWeight: "bold"
            }}>
              {getStepLabel("3_backtest_gate")}
            </div>
            <div style={{
              fontFamily: "monospace",
              fontSize: 9,
              color: "var(--atlas-text-secondary)"
            }}>
              {getStepName("3_backtest_gate")}
            </div>
            <div style={{
              fontFamily: "monospace",
              fontSize: 9,
              color: "var(--atlas-text-secondary)"
            }}>
              {getStepDescription("3_backtest_gate")}
              {getStepTime("3_backtest_gate") && (
                <span style={{ marginLeft: 8 }}>
                  {getStepTime("3_backtest_gate")}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {getStepStatus("3_backtest_gate") === "done" && (
        <>
          <div style={{
            display: "flex",
            alignItems: "center",
            marginBottom: 16,
            borderBottom: "1px solid var(--atlas-border)",
            paddingBottom: 8
          }}>
            <span style={{
              fontFamily: "monospace",
              fontSize: 14,
              fontWeight: "bold",
              color: "var(--atlas-text)"
            }}>
              Parametrização
            </span>
            <span style={{
              marginLeft: 8,
              fontFamily: "monospace",
              fontSize: 11,
              color: "var(--atlas-text-secondary)"
            }}>
              {ticker}
            </span>
          </div>

          {/* Sub-título dinâmico */}
          <div style={{
            fontFamily: "monospace",
            fontSize: 10,
            color: "var(--atlas-text-secondary)",
            marginTop: 2
          }}>
{faseCalibracao === "integridade" && "Integridade de dados"}
{faseCalibracao === "indexacao" && "Indexação"}
{faseCalibracao === "otimizacao" && "Otimização"}
</div>

{/* Valores de parametrização em azul */}
{parametros.take_profit !== null && parametros.stop_loss !== null && (
  <div style={{
    fontFamily: "monospace",
    fontSize: 9,
    color: "var(--atlas-blue)",
    marginTop: 6
  }}>
    TP: {parametros.take_profit.toFixed(2)} | STOP: {parametros.stop_loss.toFixed(2)}
  </div>
)}
</>
)}

      {/* Botão de reinício apenas em caso de erro - não mostra "Iniciar" pois já foi iniciado na aba Gestão */}

      {getStepStatus("1_backtest_dados") === "error" && (
        <button
          onClick={handleIniciar}
          style={{
            width: "100%",
            padding: "8px 16px",
            background: "var(--atlas-blue)",
            border: "none",
            color: "#fff",
            fontFamily: "monospace",
            fontSize: 11,
            borderRadius: 4,
            cursor: "pointer",
            marginBottom: 8
          }}
        >
          Reiniciar Step 1
        </button>
      )}

      {getStepStatus("2_tune") === "error" && (
        <button
          onClick={handleIniciar}
          style={{
            width: "100%",
            padding: "8px 16px",
            background: "var(--atlas-blue)",
            border: "none",
            color: "#fff",
            fontFamily: "monospace",
            fontSize: 11,
            borderRadius: 4,
            cursor: "pointer",
            marginBottom: 8
          }}
        >
          Reiniciar Step 2
        </button>
      )}

      {getStepStatus("3_backtest_gate") === "error" && (
        <button
          onClick={handleIniciar}
          style={{
            width: "100%",
            padding: "8px 16px",
            background: "var(--atlas-blue)",
            border: "none",
            color: "#fff",
            fontFamily: "monospace",
            fontSize: 11,
            borderRadius: 4,
            cursor: "pointer",
            marginBottom: 8
          }}
        >
          Reiniciar Step 3
        </button>
      )}
    </div><style>{`
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
      }
    `}}</style></>
  );
}