import React, { useState, useEffect } from "react";
import { useSystemStore } from "../../store/systemStore";

export default function OnboardingDrawer({ ticker, onClose }) {
  const [onboarding, setOnboarding] = useState(null);
  const [watchdogAlert, setWatchdogAlert] = useState(null);
  const tuneProgress = useSystemStore(s => s.tuneProgress);
  
  // Carregar estado inicial do onboarding
  useEffect(() => {
    const fetchOnboarding = async () => {
      try {
        const res = await fetch(`/delta-chaos/onboarding/${ticker}`);
        if (res.ok) {
          const data = await res.json();
          setOnboarding(data);
        }
      } catch (error) {
        console.error("Erro ao carregar onboarding:", error);
      }
    };
    
    fetchOnboarding();
    
    // Atualizar periodicamente
    const interval = setInterval(fetchOnboarding, 5000);
    return () => clearInterval(interval);
  }, [ticker]);
  
  // Monitorar progresso do TUNE
  useEffect(() => {
    if (tuneProgress && tuneProgress.ticker === ticker) {
      setOnboarding(prev => {
        if (!prev) return prev;
        const newOnboarding = { ...prev };
        newOnboarding.steps["2_tune"].trials_completos = tuneProgress.trialNumber;
        newOnboarding.steps["2_tune"].best_ir = tuneProgress.bestIr;
        return newOnboarding;
      });
    }
  }, [tuneProgress, ticker]);
  
  // Watchdog: alerta se sem sinal por 5 minutos
  useEffect(() => {
    if (!onboarding) return;
    
    const step2 = onboarding.steps["2_tune"];
    if (step2.status === "running" && onboarding.ultimo_evento_em) {
      const lastEvent = new Date(onboarding.ultimo_evento_em);
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
      
      if (lastEvent < fiveMinutesAgo && !watchdogAlert) {
        setWatchdogAlert("Processo sem sinal há 5 minutos — verifique o terminal");
      } else if (lastEvent >= fiveMinutesAgo && watchdogAlert) {
        setWatchdogAlert(null);
      }
    }
  }, [onboarding, watchdogAlert]);
  
  const getStepStatus = (stepKey) => {
    if (!onboarding) return "idle";
    return onboarding.steps[stepKey]?.status || "idle";
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
    if (status === "done" && onboarding?.steps[stepKey]?.concluido_em) {
      return new Date(onboarding.steps[stepKey].concluido_em).toLocaleString("pt-BR");
    }
    return "";
  };
  
  const handleRetomar = async () => {
    try {
      const res = await fetch(`/delta-chaos/onboarding/${ticker}/retomar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      if (res.ok) {
        const data = await res.json();
        // Atualizar estado
        setOnboarding(prev => {
          if (!prev) return prev;
          const newOnboarding = { ...prev };
          newOnboarding.steps["2_tune"].status = "running";
          newOnboarding.steps["2_tune"].iniciado_em = new Date().toISOString();
          newOnboarding.ultimo_evento_em = new Date().toISOString();
          return newOnboarding;
        });
      }
    } catch (error) {
      console.error("Erro ao retomar:", error);
    }
  };
  
  const handleIniciar = async () => {
    try {
      const res = await fetch("/delta-chaos/onboarding/iniciar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker, confirm: true, description: "Iniciar onboarding" })
      });
      if (res.ok) {
        const data = await res.json();
        // Atualizar estado
        setOnboarding(prev => {
          if (!prev) return prev;
          const newOnboarding = { ...prev };
          newOnboarding.step_atual = 1;
          newOnboarding.steps["1_backtest_dados"].status = "running";
          newOnboarding.steps["1_backtest_dados"].iniciado_em = new Date().toISOString();
          newOnboarding.ultimo_evento_em = new Date().toISOString();
          return newOnboarding;
        });
      }
    } catch (error) {
      console.error("Erro ao iniciar:", error);
    }
  };
  
  if (!onboarding) return null;
  
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
            Step {onboarding.step_atual}
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
            Step {onboarding.step_atual + 1}
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
            Step {onboarding.step_atual + 2}
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
                    {onboarding.steps["2_tune"].trials_completos || 0} / {onboarding.steps["2_tune"].trials_total} trials
                  </span>
                  <span style={{
                    fontFamily: "monospace",
                    fontSize: 9,
                    color: "var(--atlas-text-secondary)"
                  }}>
                    IR: {onboarding.steps["2_tune"].best_ir?.toFixed(4) || "0.0000"}
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
                    width: `${(onboarding.steps["2_tune"].trials_completos || 0) / onboarding.steps["2_tune"].trials_total * 100}%`
                  }} />
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
              onClick={() => {
                // Implementar confirmação de entrada em OPERAR
                alert("Confirmação de entrada em OPERAR implementada");
                onClose();
              }}
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
              onClick={() => {
                // Implementar manter em MONITORAR
                alert("Manter em MONITORAR implementado");
                onClose();
              }}
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