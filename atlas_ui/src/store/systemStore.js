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
  orchestratorAtivo: false,
  progresso: null,
  digestItems: [],
  digestTimestamp: null,

  updateFromEvent: (event) => set((state) => {
    switch (event.type) {
      case "health_update":
        return {
          health: event.data?.health || "unknown",
          health_reason: event.data?.health_reason || ""
        };
      case "health":
        return { health: event.status };
      case "module_status":
        return {
          modules: {
            ...state.modules,
            [event.module]: event.status,
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
      case "orchestrator_start":
        return { orchestratorAtivo: true, progresso: null };
      case "orchestrator_progress":
        return { progresso: event.data || null };
      case "orchestrator_done":
        return {
          orchestratorAtivo: false,
          progresso: null,
          digestItems: event.data?.items || [],
          digestTimestamp: event.data?.timestamp || new Date().toISOString(),
        };
      case "orchestrator_error":
        return { orchestratorAtivo: false, progresso: null };
      default:
        return state;
    }
  }),
}));