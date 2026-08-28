import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://0.0.0.0:7860",
        changeOrigin: true,
      },
      "/start": {
        target: "http://0.0.0.0:7860",
        changeOrigin: true,
      },
      "/sessions": {
        target: "http://0.0.0.0:7860",
        changeOrigin: true,
      },
    },
  },
});
