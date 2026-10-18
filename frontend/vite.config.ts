import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// The browser talks only to this server; /api is passed through to the API container,
// so a single port is exposed (atlas plate 04).
const apiTarget = process.env.API_URL ?? "http://api:8000";
const passApiThrough = { "/api": { target: apiTarget, changeOrigin: true } };

export default defineConfig({
  plugins: [react()],
  server: { proxy: passApiThrough },
  preview: { proxy: passApiThrough },
  test: { environment: "jsdom", globals: true, setupFiles: ["./src/testSetup.ts"] },
});
