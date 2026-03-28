// atlas_ui/src/store/analyticsStore.js
import { create } from "zustand";

export const useAnalyticsStore = create((set, get) => ({
  distribution: null,
  acf: null,
  fatTails: null,
  walkForward: null,
  staleness: 0,
  
  setAnalytics: (data) => set({
    distribution: data.distribution || null,
    acf: data.acf || null,
    // ✅ Aceita BOTH snake_case e camelCase
    fatTails: data.fatTails || data.fat_tails || null,
    walkForward: data.walkForward || data.walk_forward || null,
    staleness: Date.now(),
  }),
  
  clear: () => set({
    distribution: null,
    acf: null,
    fatTails: null,
    walkForward: null,
    staleness: 0,
  }),
  
  update: (event) => {
    if (event.type === "cycle_update") {
      set({ staleness: Date.now() });
    }
  },
}));