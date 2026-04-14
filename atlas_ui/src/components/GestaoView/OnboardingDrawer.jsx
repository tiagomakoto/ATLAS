import React, { useState, useEffect } from "react";
import useWebSocket from "../../hooks/useWebSocket";

export default function OnboardingDrawer({ ticker, onClose }) {
  const [onboarding, setOnboarding] = useState(null);
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
  
  // Carregar estado inicial do onboarding
  useEffect(() => {
    const fetchOnboarding = async () => {
      try {
        const res = await fetch(`/delta-chaos/onboarding/${ticker}`);
        if (res.ok) {
          const data = await res.json();
          setOnboarding(data);
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
        console.error("Erro ao carregar onboarding:", error);
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

  // Conexão WebSocket para eventos em tempo real
  const wsUrl = `ws://${window.location.hostname}:${window.location.port || '8000'}/ws/events`;
  useWebSocket(wsUrl, (evento) => {
    handleEvento(evento);
  });

  const handleEvento = (evento) => {
    console.log("[ONBOARDING] Evento recebido:", evento.type, evento.data);
    
    const stepMap = {
      "ORBIT": "1_backtest_dados",
      "TUNE": "2_tune",
      "GATE": "3_backtest_gate"
    };
    
    if (evento.type === "dc_module_start") {
      const modulo = evento.data?.modulo;
      const stepKey = stepMap[modulo];
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
        }
      }
    }

    if (evento.type === "dc_module_complete") {
      const modulo = evento.data?.modulo;
      const status = evento.data?.status;
      const stepKey = stepMap[modulo];
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
    }

    if (evento.type === "terminal_log") {
      const msg = evento.data.message;
      const match = msg.match(/TUNE \[\w+\] trial (\d+)\/(\d+) best_ir=([+-]?\d+\.\d+)/);
      if (match) {
        setTrialAtual(parseInt(match[1]));
        setTrialTotal(parseInt(match[2]));
        setBestIr(parseFloat(match[3]));
        setUltimoEventoEm(Date.now());
      }
    }
  };

  const getStepStatus = (stepKey) => {
    return steps[stepKey]?.status || "idle";
  };

  const getStepLabel = (stepKey) => {
    const status = getStepStatus(stepKey);
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
    const colors = {
      idle: "rgba(156,163,175,0.1)",
      running: "rgba(59,130,246,0.1)",
      done: "rgba(34,197,94,0.1)",
      error: "rgba(239,68,68,0.1)",
      paused: "rgba(245,158,11,0.1)"
    };
    return colors[status] || "rgba(156,163,175,0.1)";
  };

  const getStepDescription = (stepKey) => {
    const status = getStepStatus(stepKey);
    const descriptions = {
      idle: "Aguardando início",
      running: "Em execução",
      done: "Concluído",
      error: "Falhou",
      paused: "Pausado"
    };
    return descriptions[status] || "Aguardando início";
  };

  const getStepTime = (stepKey) => {
    const status = getStepStatus(stepKey);
    if (status === "done" && steps[stepKey]?.concluido_em) {
      return new Date(steps[stepKey].concluido_em).toLocaleString("pt-BR");
    }
    return "";
  };

  const handleRetomar = async () => {
    try {
      const res = await fetch(`/delta-chaos/onboarding/${ticker}/retomar`, {
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
        console.error("Erro ao retomar onboarding:", res.statusText);
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
    try {
      const res = await fetch("/delta-chaos/onboarding/iniciar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker, confirm: true, description: "Iniciar onboarding" })
      });
      if (!res.ok) {
        // Apenas em caso de erro, atualizar estado
        setSteps(prev => ({
          ...prev,
          "1_backtest_dados": {
            ...prev["1_backtest_dados"],
            status: "error"
          }
        }));
        console.error("Erro ao iniciar onboarding:", res.statusText);
      }
      // Em caso de sucesso, NÃO atualizar - aguardar evento WebSocket
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
      const res = await fetch("http://localhost:8000/ativos/" + ticker + "/status", {
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
  // if (!onboarding) return null;

  return (
    <div style={{
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
          ONBOARDING — {ticker}
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
          marginBottom: 8
        }}>
          <span style={{
            fontFamily: "monospace",
            fontSize: 11,
            color: "var(--atlas-text-secondary)"
          }}>
            Step {getStepStatus("1_backtest_dados") === "done" ? 1 : getStepStatus("1_backtest_dados") === "running" ? 1 : getStepStatus("2_tune") === "running" ? 2 : getStepStatus("3_backtest_gate") === "running" ? 3 : 1}
          </span>
          <span style={{
            margin: "0 8px",
            color: "var(--atlas-text-secondary)"
          }}>
            •
          </span>
          <span style={{
            fontFamily: "monospace",
            fontSize: 11,
            color: "var(--atlas-text-secondary)"
          }}>
            {getStepLabel("1_backtest_dados")}
          </span>
        </div>
        
        <div style={{
          display: "flex",
          alignItems: "center",
          marginBottom: 8
        }}>
          <span style={{
            fontFamily: "monospace",
            fontSize: 11,
            color: "var(--atlas-text-secondary)"
          }}>
            Step {getStepStatus("1_backtest_dados") === "done" ? 2 : getStepStatus("2_tune") === "running" ? 2 : getStepStatus("3_backtest_gate") === "running" ? 3 : 1}
          </span>
          <span style={{
            margin: "0 8px",
            color: "var(--atlas-text-secondary)"
          }}>
            •
          </span>
          <span style={{
            fontFamily: "monospace",
            fontSize: 11,
            color: "var(--atlas-text-secondary)"
          }}>
            {getStepLabel("2_tune")}
          </span>
        </div>
        
        <div style={{
          display: "flex",
          alignItems: "center",
          marginBottom: 8
        }}>
          <span style={{
            fontFamily: "monospace",
            fontSize: 11,
            color: "var(--atlas-text-secondary)"
          }}>
            Step {getStepStatus("2_tune") === "done" ? 3 : getStepStatus("3_backtest_gate") === "running" ? 3 : 2}
          </span>
          <span style={{
            margin: "0 8px",
            color: "var(--atlas-text-secondary)"
          }}>
            •
          </span>
          <span style={{
            fontFamily: "monospace",
            fontSize: 11,
            color: "var(--atlas-text-secondary)"
          }}>
            {getStepLabel("3_backtest_gate")}
          </span>
        </div>
      </div>
      
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
          borderRadius: 4
        }}>
          <span style={{
            fontSize: 14,
            color: getStepColor("1_backtest_dados"),
            fontWeight: "bold",
            marginRight: 8
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
          borderRadius: 4
        }}>
          <span style={{
            fontSize: 14,
            color: getStepColor("2_tune"),
            fontWeight: "bold",
            marginRight: 8
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
              {getStepDescription("2_tune")}
              {getStepTime("2_tune") && (
                <span style={{ marginLeft: 8 }}>
                  {getStepTime("2_tune")}
                </span>
              )}
            </div>
            
            {getStepStatus("2_tune") === "running" && (
              <div style={{
                marginTop: 8,
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
                    IR: {bestIr.toFixed(4) || "0.0000"}
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
                    width: `${trialAtual / trialTotal * 100}%`
                  }} />
                </div>
                
                {/* Tempo decorrido e estimativas */}
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
              </div>
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
          borderRadius: 4
        }}>
          <span style={{
            fontSize: 14,
            color: getStepColor("3_backtest_gate"),
            fontWeight: "bold",
            marginRight: 8
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
        <div style={{
          background: "var(--atlas-surface)",
          padding: 12,
          borderRadius: 4,
          marginBottom: 16,
          border: "1px solid var(--atlas-blue)"
        }}>
          <h4 style={{
            margin: "0 0 8px 0",
            fontFamily: "monospace",
            fontSize: 11,
            color: "var(--atlas-blue)"
          }}>
            Conclusão do Onboarding
          </h4>
          <p style={{
            fontFamily: "monospace",
            fontSize: 10,
            color: "var(--atlas-text-secondary)",
            marginBottom: 12
          }}>
            {ticker} aprovado pelo GATE — confirmar entrada em OPERAR?
          </p>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={handleConfirmarOperar}
              style={{
                flex: 1,
                padding: "6px 12px",
                background: "var(--atlas-green)",
                border: "none",
                color: "#fff",
                fontFamily: "monospace",
                fontSize: 10,
                borderRadius: 2,
                cursor: "pointer"
              }}
            >
              Confirmar entrada
            </button>
            <button
              onClick={onClose}
              style={{
                flex: 1,
                padding: "6px 12px",
                background: "var(--atlas-amber)",
                border: "none",
                color: "#fff",
                fontFamily: "monospace",
                fontSize: 10,
                borderRadius: 2,
                cursor: "pointer"
              }}
            >
              Manter em MONITORAR
            </button>
          </div>
        </div>
      )}
      
      {getStepStatus("1_backtest_dados") === "idle" && (
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
          Iniciar Onboarding
        </button>
      )}
      
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
    </div>
  );
}