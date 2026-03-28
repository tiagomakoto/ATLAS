import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/config":  { target: "http://localhost:8000", changeOrigin: true },
      "/mode":    { target: "http://localhost:8000", changeOrigin: true },
      "/modules": { target: "http://localhost:8000", changeOrigin: true },
      "/report":  { target: "http://localhost:8000", changeOrigin: true },
      "/ws":      { target: "ws://localhost:8000", ws: true, changeOrigin: true },
    },
  },
});
