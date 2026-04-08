// atlas_ui/src/store/systemStore.js
import { create } from "zustand";

export const useSystemStore = create((set) => ({
  health: "ok",
  health_reason: "",
  modules: {},
  cycle: {},
  events: [],
  regime: null,
  alert: null,
  // v2.5.2 — campos do Orquestrador
  dailyAtivo: false,
  dailyConcluido: false,
  progresso: null,
  digestItems: [],
  digestTimestamp: null,
  // v2.6 — digest por ativo + transições de status
  digestPorAtivo: {},
  cicloNovo: false,
  statusTransitions: [],

  updateFromEvent: (event) => set((state) => {
    switch (event.type) {
      case "health_update":
        return {
          health: event.data?.health || "unknown",
          health_reason: event.data?.health_reason || ""
        };
      case "health":
        return { health: event.status };
      // v2.6 — eventos dc_module (TAPE, ORBIT, GATE, etc) via WebSocket
      case "dc_module_complete":
      case "dc_module_start":
        return {
          modules: {
            ...state.modules,
            [event.data?.ticker || "global"]: {
              ...(state.modules[event.data?.ticker || "global"] || {}),
              [event.data?.modulo]: event.data?.status,
            },
          },
        };
      case "cycle_update":
        return { cycle: event.data || {} };
      case "event":
        return { events: [event, ...state.events].slice(0, 50) };
      case "regime_update":
        return { regime: event };
      case "alert":
        return { alert: event };
      // v2.5.2 — eventos do Orquestrador
      case "daily_start":
        return {
          dailyAtivo: true,
          dailyConcluido: false,
          progresso: null,
          modules: {},  // ← limpa todas as luzes ao iniciar
          digestPorAtivo: {},
          cicloNovo: false,
          statusTransitions: []
        };
      case "daily_progress":
        return { progresso: event.data || null };
      case "daily_done":
        return {
          dailyAtivo: false,
          dailyConcluido: true,
          progresso: null,
          digestItems: event.data?.items || [],
          digestTimestamp: event.data?.timestamp || new Date().toISOString(),
        };
        case "daily_error":
          return { dailyAtivo: false, progresso: null };
        case "status_transition":
         return {
           statusTransitions: [...state.statusTransitions, event]
         };
       // #3 FIX: Handler para atualizar digest por ativo durante o ciclo
       case "daily_ativo_complete":
         return {
           digestPorAtivo: {
             ...state.digestPorAtivo,
             [event.data?.ticker]: event.data?.digest || {}
           }
         };
       default:
        return state;
    }
  }),
}));