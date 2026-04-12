// atlas_ui/src/components/OrchestratorLogDrawer.jsx
import React, { useState, useEffect, useRef } from "react";

const MODULOS = [
  { id: "GATE", label: "GATE", icon: "●", iconOk: "✓", iconErr: "✗" },
  { id: "XLSX", label: "XLSX EOD", icon: "●", iconOk: "✓", iconErr: "✗" },
  { id: "TP_STOP", label: "TP / STOP", icon: "●", iconOk: "✓", iconErr: "✗" },
  { id: "TAPE", label: "TAPE", icon: "●", iconOk: "✓", iconErr: "✗" },
  { id: "ORBIT", label: "ORBIT", icon: "●", iconOk: "✓", iconErr: "✗" },
  { id: "REFLECT", label: "REFLECT", icon: "●", iconOk: "✓", iconErr: "✗" },
];

// ─────────────────────────────────────────────────────────────────────────────
// PROCESSADOR DE EVENTOS ESTRUTURADOS DO DELTA CHAOS
// ─────────────────────────────────────────────────────────────────────────────
// Esta função substitui o parsing frágil de texto para determinar o status
// dos módulos. Ela processa eventos JSON estruturados emitidos pelo backend
// via event_bus.py -> dc_runner.py -> WebSocket -> frontend.
//
// Formato esperado:
//   { type: "dc_module_start" | "dc_module_complete" | "dc_module_error" | "dc_workflow_complete",
//     data: { modulo: "ORBIT", status: "ok", ... } }
//
// COMENTÁRIO CRÍTICO — NÃO REMOVER. Essa função é a base para comunicação
// confiável entre backend e frontend, eliminando dependência de texto dos logs.
// ─────────────────────────────────────────────────────────────────────────────

function processDCEvent(data, moduloAtual, setModuloAtual, setModuloStatus, setProgresso, setMensagem) {
  const { type, data: eventData } = data;
  const { modulo, status, timestamp } = eventData || {};

  if (!modulo || !MODULOS.find(m => m.id === modulo)) {
    return false; // Não é evento de módulo conhecido
  }

  const idx = MODULOS.findIndex(m => m.id === modulo);

  switch (type) {
    case "dc_module_start":
      // Marcar módulo anterior como ok se estava rodando
      setModuloAtual(prev => {
        if (prev && prev !== modulo) {
          setModuloStatus(ps => ({ ...ps, [prev]: ps[prev] === "erro" ? "erro" : "ok" }));
        }
        return modulo;
      });
      setModuloStatus(prev => ({ ...prev, [modulo]: "rodando" }));
      setProgresso(((idx + 1) / MODULOS.length) * 100);
      setMensagem(`${modulo} iniciado`);
      break;

    case "dc_module_complete":
      setModuloStatus(prev => ({
        ...prev,
        [modulo]: status === "ok" ? "ok" : "erro"
      }));
      if (status === "ok" && moduloAtual === modulo) {
        setModuloAtual(null);
      }
      setProgresso(((idx + 1) / MODULOS.length) * 100);
      setMensagem(`${modulo} ${status === "ok" ? "concluído" : "falhou"}`);
      break;

    case "dc_module_error":
      setModuloStatus(prev => ({ ...prev, [modulo]: "erro" }));
      setMensagem(`${modulo} erro`);
      break;

    case "dc_workflow_complete":
      setModuloStatus(prev => {
        const final = { ...prev };
        if (moduloAtual) final[moduloAtual] = final[moduloAtual] || "ok";
        return final;
      });
      setProgresso(100);
      setMensagem("Workflow concluído");
      break;

    default:
      return false;
  }

  return true;
}

function parseMessage(msg) {
  const upper = msg.toUpperCase();

  if (upper.includes("ERRO") || upper.includes("ERROR")) {
    return { modulo: null, erro: true };
  }

  if (upper.includes("TAPE") && !upper.includes("ORBIT")) {
    return { modulo: "TAPE", erro: false };
  }
  if (upper.includes("ORBIT") && !upper.includes("GATE")) {
    return { modulo: "ORBIT", erro: false };
  }
  if (upper.includes("GATE") && !upper.includes("REFLECT")) {
    return { modulo: "GATE", erro: false };
  }
  if (upper.includes("REFLECT")) {
    return { modulo: "REFLECT", erro: false };
  }

  if (upper.includes("CONCLUÍDO") || upper.includes("CONCLUIDO") ||
    upper.includes("FINALIZADO") || upper.includes("OK")) {
    return { modulo: "FINAL", erro: false };
  }

  return { modulo: null, erro: false };
}

export default function OrchestratorLogDrawer({ isRunning, isFinished, drawerEvents }) {
  const [visible, setVisible] = useState(false);
  const [moduloAtual, setModuloAtual] = useState(null);
  const [moduloStatus, setModuloStatus] = useState({});
  const [mensagem, setMensagem] = useState("");
  const [progresso, setProgresso] = useState(0);
  const [ticker, setTicker] = useState("");
  const [tickerTransition, setTickerTransition] = useState(false);
  const wsRef = useRef(null);
  const timeoutRef = useRef(null);
  const moduloAtualRef = useRef(moduloAtual);
  moduloAtualRef.current = moduloAtual;

  // ═══ NOVO: Processar eventos vindos da API (fallback via props) ═══
  useEffect(() => {
    if (drawerEvents && Array.isArray(drawerEvents)) {
      drawerEvents.forEach(evento => processarEventoDC(evento));
    }
  }, [drawerEvents]);

  // Função interna para processar eventos DC (recebe do WebSocket OU das props)
  const processarEventoDC = (data) => {
    // Terminal logs
    if (data && (data.type === "terminal_log" || data.type === "terminal_error")) {
      const logMsg = data.data?.message || data.message || "";
      if (logMsg.includes("[DAILY] Processando")) {
        setModuloStatus({});
        setModuloAtual(null);
      }
      setMensagem(logMsg);
      return;
    }

    // DC module events
    if (data && data.type && data.type.startsWith("dc_")) {
      const mod = data.data?.modulo;
      const status = data.data?.status;
      const tk = data.data?.ticker;

      if (data.type === "dc_module_start") {
        setModuloAtual(mod);
        setModuloStatus(prev => {
          if (prev[mod] === "erro") return prev;
          return { ...prev, [mod]: "rodando" };
        });
        if (tk) {
          setTicker(tk);
          setTickerTransition(true);
        }
        setMensagem(`${tk ? tk + " — " : ""}${mod} iniciado`);
        return;
      }

      if (data.type === "dc_module_complete") {
        setModuloStatus(prev => ({
          ...prev,
          [mod]: status === "ok" ? "ok" : "erro"
        }));
        setModuloAtual(null);
        if (tk) setTicker(tk);
        setProgresso(((MODULOS.findIndex(m => m.id === mod) + 1) / MODULOS.length) * 100);
        setMensagem(`${tk ? tk + " — " : ""}${mod} ${status === "ok" ? "concluído" : "falhou"} — ${data.data?.descricao || ""}`);
        return;
      }

      if (data.type === "dc_module_error") {
        setModuloStatus(prev => ({ ...prev, [mod]: "erro" }));
        setMensagem(`${mod} erro — ${data.data?.descricao || ""}`);
        return;
      }

      if (data.type === "dc_workflow_complete") {
        setModuloAtual(null);
        setProgresso(100);
        setMensagem("Ciclo concluído");
        return;
      }

      if (data.type === "daily_ativo_complete") {
        const tk = data.data?.ticker;
        setMensagem(`${tk} processado`);
        return;
      }
    }
  };

  // ═══ FIM ═══

  useEffect(() => {
    // ═══ CORRIGIDO: sempre conectar quando isRunning muda para true ═══
    if (isRunning) {
      // Sempre conectar quando o processo inicia
      // Fechar conexão anterior se existir
      if (wsRef.current) {
        wsRef.current.close();
      }
      setVisible(true);
      setMensagem("Iniciando...");
      setModuloStatus({});
      setModuloAtual(null);
      setProgresso(0);
      setTicker("");
      setTickerTransition(false);

      // Conectar WebSocket
      wsRef.current = new WebSocket("ws://localhost:8000/ws/events");

      wsRef.current.onopen = () => {
        console.log("[ORCH-WS] WebSocket conectado em /ws/events");
      };

       wsRef.current.onmessage = (event) => {
         try {
           let msg = event.data;
           let data = null;

            try {
              data = JSON.parse(msg);
              msg = data.data?.message || data.message || data.msg || msg;
            } catch { }

            // ── Terminal logs: atualizar mensagem em tempo real ──
            if (data && (data.type === "terminal_log" || data.type === "terminal_error")) {
              const logMsg = data.data?.message || msg;
              
              // #1 FIX: Detectar início de novo ativo no loop e limpar luzes
              if (logMsg.includes("[DAILY] Processando")) {
                setModuloStatus({});
                setModuloAtual(null);
              }
              
              setMensagem(logMsg);
              return;
            }

             // ── Tentar processar como evento estruturado do Delta Chaos ──
            if (data && data.type && data.type.startsWith("dc_")) {
              // Evento tem formato: { type: "dc_module_...", data: { modulo, status, ticker, ... } }
              const mod = data.data?.modulo;
              const status = data.data?.status;
              const tk = data.data?.ticker;

             // ═════════════════════════════════════════════════════════════
             // dc_module_start — any module (TAPE, ORBIT, GATE, REFLECT)
             // ═════════════════════════════════════════════════════════════
             if (data.type === "dc_module_start") {
               setModuloAtual(mod);
               setModuloStatus(prev => {
                 if (prev[mod] === "erro") return prev;
                 return { ...prev, [mod]: "rodando" };
               });
               if (tk) {
                 setTicker(tk);
                 setTickerTransition(true);
               }
               setMensagem(`${tk ? tk + " — " : ""}${mod} iniciado`);
               return;
             }

              if (data.type === "dc_module_complete") {
               setModuloStatus(prev => ({
                 ...prev,
                 [mod]: status === "ok" ? "ok" : "erro"
               }));
               setModuloAtual(null);
               if (tk) setTicker(tk);
               setProgresso(((MODULOS.findIndex(m => m.id === mod) + 1) / MODULOS.length) * 100);
               setMensagem(`${tk ? tk + " — " : ""}${mod} ${status === "ok" ? "concluído" : "falhou"} — ${data.data?.descricao || ""}`);
               return;
             }

            // Error: marcar como erro
            if (data.type === "dc_module_error") {
              setModuloStatus(prev => ({ ...prev, [mod]: "erro" }));
              setMensagem(`${mod} erro — ${data.data?.descricao || ""}`);
              return;
            }

            // Workflow complete: finalize
            if (data.type === "dc_workflow_complete") {
              setModuloAtual(null);
              setProgresso(100);
              setMensagem("Ciclo concluído");
              return;
            }

            // #3 FIX: Handler para daily_ativo_complete - atualizar digest por ativo
            if (data.type === "daily_ativo_complete") {
              const tk = data.data?.ticker;
              const digest = data.data?.digest;
              setMensagem(`${tk} processado`);
              return;
            }
          }



          // Gate EOD bloqueado → luz vermelha no GATE (antes do bloco mensal)
          if (data.gate_eod === "BLOQUEADO") {
            setModuloStatus(prev => ({ ...prev, GATE: "erro" }));
            // A mensagem específica já vem do evento dc_module_complete do gate_eod
            // Só atualizar se ainda não tiver mensagem mais específica
            setMensagem(prev => {
              if (prev.includes("desatualizado") || prev.includes("iniciando atualização") || prev.includes("dados incompletos")) {
                return prev; // Manter mensagem específica do dc_module_complete
              }
              return `${tk}: GATE EOD BLOQUEADO`;
            });
          } else if (data.gate_eod === "MONITORAR") {
            setModuloStatus(prev => ({ ...prev, GATE: "ok" }));
            setMensagem(`${tk}: GATE EOD = MONITORAR`);
          } else if (data.gate_eod === "OPERAR") {
            setModuloStatus(prev => ({ ...prev, GATE: "ok" }));
            setMensagem(`${tk}: GATE EOD = OPERAR`);
          }

          // Bloco mensal: mostrar resumo do que aconteceu
          if (data.bloco_mensal) {
            const bm = data.bloco_mensal;
            // Atualizar status dos módulos baseado no resultado do bloco mensal
            setModuloStatus(prev => {
              const next = { ...prev };
              if (bm.orbit === "ok") next.ORBIT = "ok";
              else if (typeof bm.orbit === "string" && bm.orbit.startsWith("erro")) next.ORBIT = "erro";

              if (bm.gate === "ok") next.GATE = "ok";
              else if (typeof bm.gate === "string" && bm.gate.startsWith("erro")) next.GATE = "erro";

              return next;
            });

            if (bm.tune === "executado") {
              setMensagem(`${tk}: TUNE executado — parâmetros recalibrados`);
            } else if (bm.tune && typeof bm.tune === "string" && bm.tune.startsWith("erro")) {
              setMensagem(`${tk}: TUNE erro — ${bm.tune}`);
            } else if (bm.status_anterior && bm.status_novo) {
              setMensagem(`${tk}: ${bm.status_anterior} → ${bm.status_novo}`);
            }
          }
          return;


           if (data && data.type === "status_transition") {
             const tk = data.ticker;
             setMensagem(`${tk}: ${data.status_anterior} → ${data.status_novo}`);
             return;
           }

           // ── Fallback: apenas texto legível (não JSON) ──
           if (msg && msg.trim() && !msg.trim().startsWith("{")) {
             setMensagem(msg.trim().substring(0, 120));
           }
        } catch (e) {
          console.error("WS parse error:", e);
        }
      };

      wsRef.current.onclose = () => {
        // Conexão fechada
      };
    }

    // Quando isRunning fica false, NÃO fechar mais automaticamente
    // (removido temporariamente para debug)
    /*
    if (!isRunning && visible) {
      setVisible(false);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      clearTimeout(timeoutRef.current);
    }
    */

    return () => {
      // Apenas limpar timeouts — NÃO fechar WebSocket aqui
      clearTimeout(timeoutRef.current);
      // O WebSocket será fechado pelo handleClose ou quando o componente desmontar
    };
  }, [isRunning]);

  // #1 FIX: Reset lights when process restarts (detect false → true transition)
  const prevIsRunningRef = useRef(isRunning);
  useEffect(() => {
    const wasRunning = prevIsRunningRef.current;
    const isNowRunning = isRunning;

    // Limpar luzes quando isRunning muda de false para true
    // Não依赖 visible porque visible pode ser false no momento do clique
    if (isNowRunning && !wasRunning) {
      // Processo acabou de iniciar (transição false → true) - limpar luzes
      setModuloStatus({});
      setModuloAtual(null);
      setProgresso(0);
      setTicker("");
      setTickerTransition(false);
      setMensagem("Iniciando ciclo...");
    }

    prevIsRunningRef.current = isNowRunning;
  }, [isRunning]);

  const handleClose = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setVisible(false);
    clearTimeout(timeoutRef.current);
  };

  const getStatus = (moduloId) => {
    if (moduloStatus[moduloId] === "erro") return "erro";
    if (moduloStatus[moduloId] === "ok") return "ok";
    if (moduloId === moduloAtual) return "rodando";
    return "espera";
  };

  const getIcon = (modulo, status) => {
    const m = MODULOS.find(x => x.id === modulo);
    if (status === "ok") return m.iconOk;
    if (status === "erro") return m.iconErr;
    if (status === "rodando") return m.icon;
    return m.icon;
  };

  const getColor = (status, modulo) => {
    // Cores customizadas para XLSX
    if (modulo === "XLSX") {
      if (status === "ok") return "var(--atlas-green)";
      if (status === "erro") return "var(--atlas-amber)";  // Amarelo para "não encontrado"
      if (status === "rodando") return "var(--atlas-blue)";
      return "var(--atlas-text-secondary)";
    }
    // Cores customizadas para TP_STOP
    if (modulo === "TP_STOP") {
      if (status === "ok") return "var(--atlas-green)";
      if (status === "erro") return "var(--atlas-red)";  // Vermelho para TP/STOP atingido ou sem XLSX
      if (status === "rodando") return "var(--atlas-blue)";
      return "var(--atlas-text-secondary)";
    }
    // Cores padrão para outros módulos
    if (status === "ok") return "var(--atlas-green)";
    if (status === "erro") return "var(--atlas-red)";
    if (status === "rodando") return "var(--atlas-blue)";
    return "var(--atlas-text-secondary)";
  };

  if (!visible) return null;

  return (
    <div style={{
      position: "relative",
      marginTop: -8,
      background: "#0a0a0a",
      border: "1px solid var(--atlas-border)",
      borderTop: "none",
      borderRadius: "0 0 2px 2px",
      overflow: "hidden",
      animation: "slideUp 0.3s ease"
    }}>
      {/* Barra de progresso no topo */}
      <div style={{
        height: 2,
        background: "var(--atlas-border)",
        position: "relative"
      }}>
        <div style={{
          position: "absolute",
          left: 0,
          top: 0,
          height: "100%",
          width: `${progresso}%`,
          background: "var(--atlas-blue)",
          transition: "width 0.3s ease"
        }} />
      </div>

      {/* Botão de fechar — só aparece após concluir todos os ativos */}
      {isFinished && (
        <button
          onClick={handleClose}
          style={{
            position: "absolute",
            top: 8,
            right: 8,
            background: "transparent",
            border: "none",
            color: "var(--atlas-text-secondary)",
            cursor: "pointer",
            fontSize: 14,
            fontFamily: "monospace",
            padding: 2,
            zIndex: 10
          }}
        >
          ×
        </button>
      )}

      {/* Cards de Status dos Módulos */}
      <div style={{
        display: "flex",
        gap: 8,
        padding: "12px 14px",
        borderBottom: "1px solid var(--atlas-border)"
      }}>
        {/* Grupo 1: TAPE, ORBIT, REFLECT, GATE */}
        {["TAPE", "ORBIT", "REFLECT", "GATE"].map(modId => {
          const mod = MODULOS.find(m => m.id === modId);
          const status = getStatus(modId);
          return (
            <div
              key={modId}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "4px 10px",
                background: status === "rodando" ? "rgba(59,130,246,0.15)" : "transparent",
                border: `1px solid ${status === "rodando" ? "var(--atlas-blue)" : "transparent"}`,
                borderRadius: 2,
                opacity: status === "espera" ? 0.5 : 1
              }}
            >
              <span style={{
                color: getColor(status, modId),
                fontSize: 10,
                animation: status === "rodando" ? "pulse 1s infinite" : "none"
              }}>
                {getIcon(modId, status)}
              </span>
              <span style={{
                fontFamily: "monospace",
                fontSize: 9,
                color: getColor(status, modId),
                textTransform: "uppercase"
              }}>
                {mod?.label || modId}
              </span>
            </div>
          );
        })}

        {/* Espaço entre grupos (espaço triplo) */}
        <div style={{ width: 24 }} />

        {/* Grupo 2: XLSX EOD */}
        {["XLSX"].map(modId => {
          const mod = MODULOS.find(m => m.id === modId);
          const status = getStatus(modId);
          return (
            <div
              key={modId}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "4px 10px",
                background: status === "rodando" ? "rgba(59,130,246,0.15)" : "transparent",
                border: `1px solid ${status === "rodando" ? "var(--atlas-blue)" : "transparent"}`,
                borderRadius: 2,
                opacity: status === "espera" ? 0.5 : 1
              }}
            >
              <span style={{
                color: getColor(status, modId),
                fontSize: 10,
                animation: status === "rodando" ? "pulse 1s infinite" : "none"
              }}>
                {getIcon(modId, status)}
              </span>
              <span style={{
                fontFamily: "monospace",
                fontSize: 9,
                color: getColor(status, modId),
                textTransform: "uppercase"
              }}>
                {mod?.label || modId}
              </span>
            </div>
          );
        })}

        {/* Espaço entre grupos (espaço triplo) */}
        <div style={{ width: 24 }} />

        {/* Grupo 3: TP/STOP */}
        {["TP_STOP"].map(modId => {
          const mod = MODULOS.find(m => m.id === modId);
          const status = getStatus(modId);
          return (
            <div
              key={modId}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "4px 10px",
                background: status === "rodando" ? "rgba(59,130,246,0.15)" : "transparent",
                border: `1px solid ${status === "rodando" ? "var(--atlas-blue)" : "transparent"}`,
                borderRadius: 2,
                opacity: status === "espera" ? 0.5 : 1
              }}
            >
              <span style={{
                color: getColor(status, modId),
                fontSize: 10,
                animation: status === "rodando" ? "pulse 1s infinite" : "none"
              }}>
                {getIcon(modId, status)}
              </span>
              <span style={{
                fontFamily: "monospace",
                fontSize: 9,
                color: getColor(status, modId),
                textTransform: "uppercase"
              }}>
                {mod?.label || modId}
              </span>
            </div>
          );
        })}
      </div>

      {/* Área de Mensagem Atual */}
      <div style={{
        padding: "14px",
        fontFamily: "monospace",
        fontSize: 11,
        color: "#aaa",
        minHeight: 40,
        display: "flex",
        alignItems: "center",
        gap: 8
      }}>
        {ticker && !isFinished && (
          <span style={{
            color: "var(--atlas-blue)",
            fontSize: 10,
            padding: "2px 6px",
            border: "1px solid var(--atlas-blue)",
            borderRadius: 2,
            animation: (tickerTransition && !isFinished) ? "pulse 1s infinite" : "none"
          }}>
            {ticker}
          </span>
        )}
        <span style={{ color: "#fff" }}>
          {mensagem || "Aguardando..."}
        </span>
      </div>

      <style>{`
        @keyframes slideUp {
          from { max-height: 0; opacity: 0; }
          to { max-height: 200px; opacity: 1; }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}