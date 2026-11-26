import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// The proxy forwards every request that starts with /api to the FastAPI server.
// This way the browser thinks frontend and backend share one address (no CORS trouble in dev).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": process.env.VITE_BACKEND_URL || "http://localhost:8000",
    },
  },
});
