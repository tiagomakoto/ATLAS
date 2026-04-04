// atlas_ui/src/components/OrchestratorLogDrawer.jsx
import React, { useState, useEffect, useRef } from "react";

const MODULOS = [
  { id: "TAPE",  label: "TAPE",  icon: "●", iconOk: "✓", iconErr: "✗" },
  { id: "ORBIT", label: "ORBIT", icon: "●", iconOk: "✓", iconErr: "✗" },
  { id: "FIRE",  label: "FIRE",  icon: "●", iconOk: "✓", iconErr: "✗" },
  { id: "GATE",  label: "GATE",  icon: "●", iconOk: "✓", iconErr: "✗" },
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

function processDCEvent(data, setModuloAtual, setModuloStatus, setProgresso, setMensagem) {
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
  if (upper.includes("ORBIT") && !upper.includes("FIRE") && !upper.includes("GATE")) {
    return { modulo: "ORBIT", erro: false };
  }
  if (upper.includes("FIRE")) {
    return { modulo: "FIRE", erro: false };
  }
  if (upper.includes("GATE") || upper.includes("REFLECT")) {
    return { modulo: "GATE", erro: false };
  }
  
  if (upper.includes("CONCLUÍDO") || upper.includes("CONCLUIDO") || 
      upper.includes("FINALIZADO") || upper.includes("OK")) {
    return { modulo: "FINAL", erro: false };
  }
  
  return { modulo: null, erro: false };
}

export default function OrchestratorLogDrawer({ isRunning }) {
  const [visible, setVisible] = useState(false);
  const [moduloAtual, setModuloAtual] = useState(null);
  const [moduloStatus, setModuloStatus] = useState({});
  const [mensagem, setMensagem] = useState("");
  const [progresso, setProgresso] = useState(0);
  const wsRef = useRef(null);
  const timeoutRef = useRef(null);

  useEffect(() => {
    if (isRunning && !visible) {
      setVisible(true);
      setMensagem("Iniciando...");
      setModuloStatus({});
      setModuloAtual(null);
      setProgresso(0);
      
      // Conectar WebSocket
      wsRef.current = new WebSocket("ws://localhost:8000/ws/logs");
      
      wsRef.current.onmessage = (event) => {
        try {
          let msg = event.data;
          let data = null;
          
          try {
            data = JSON.parse(msg);
            msg = data.message || data.msg || msg;
          } catch {}
          
          // ── Tentar processar como evento estruturado do Delta Chaos ──
          if (data && data.type && data.type.startsWith("dc_")) {
            const handled = processDCEvent(
              data, 
              setModuloAtual, 
              setModuloStatus, 
              setProgresso, 
              setMensagem
            );
            if (handled) {
              // Evento processado com sucesso — não fazer fallback para texto
              return;
            }
          }
          
          // ── Fallback: parsing de texto legado ──
          const { modulo, erro } = parseMessage(msg);
          
          if (erro) {
            if (moduloAtual) {
              setModuloStatus(prev => ({ ...prev, [moduloAtual]: "erro" }));
            }
          } else if (modulo && modulo !== "FINAL") {
            // Marcar módulo anterior como concluído se existia
            if (moduloAtual && moduloAtual !== modulo) {
              setModuloStatus(prev => ({ 
                ...prev, 
                [moduloAtual]: modulo === moduloAtual ? "ok" : prev[moduloAtual] || "ok" 
              }));
            }
            setModuloAtual(modulo);
            
            // Calcular progresso baseado no módulo
            const idx = MODULOS.findIndex(m => m.id === modulo);
            if (idx >= 0) {
              setProgresso(((idx + 1) / MODULOS.length) * 100);
            }
          } else if (modulo === "FINAL") {
            setModuloStatus(prev => {
              const final = { ...prev };
              if (moduloAtual) final[moduloAtual] = "ok";
              return final;
            });
            setProgresso(100);
          }
          
          setMensagem(msg);
        } catch (e) {
          console.error("WS parse error:", e);
        }
      };
      
      wsRef.current.onclose = () => {
        // Conexão fechada
      };
    }
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [isRunning]);

  useEffect(() => {
    // Quando para de rodar, esperar 3 segundos e fechar
    if (!isRunning && visible) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        setVisible(false);
      }, 3000);
    }
    
    return () => clearTimeout(timeoutRef.current);
  }, [isRunning, visible]);

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

  const getColor = (status) => {
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

      {/* Botão de fechar */}
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

      {/* Cards de Status dos Módulos */}
      <div style={{
        display: "flex",
        gap: 8,
        padding: "12px 14px",
        borderBottom: "1px solid var(--atlas-border)"
      }}>
        {MODULOS.map(mod => {
          const status = getStatus(mod.id);
          return (
            <div
              key={mod.id}
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
                color: getColor(status),
                fontSize: 10,
                animation: status === "rodando" ? "pulse 1s infinite" : "none"
              }}>
                {getIcon(mod.id, status)}
              </span>
              <span style={{
                fontFamily: "monospace",
                fontSize: 9,
                color: getColor(status),
                textTransform: "uppercase"
              }}>
                {mod.label}
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
        alignItems: "center"
      }}>
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