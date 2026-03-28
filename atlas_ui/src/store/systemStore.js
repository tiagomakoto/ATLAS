// atlas_ui/src/store/systemStore.js
import { create } from "zustand";

export const useSystemStore = create((set) => ({
  health: "ok",  // ✅ "ok" não "green"
  health_reason: "",  // ✅ NOVO
  modules: {},
  cycle: {},
  events: [],
  regime: null,
  alert: null,
  
  updateFromEvent: (event) => set((state) => {
    switch (event.type) {
      case "health_update":  // ✅ NOVO
        return {
          health: event.data?.health || "unknown",
          health_reason: event.data?.health_reason || ""
        };
      
      case "health":  // Legado
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
      
      default:
        return state;
    }
  }),
}));