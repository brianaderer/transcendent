import { defineConfig } from "orval";

// The typed API client is generated from the backend's own description (atlas OPEN-1).
// Refresh openapi.json from the running app, then regenerate: see docs/architecture/frontend.md.
export default defineConfig({
  voices: {
    input: "./openapi.json",
    output: {
      target: "./src/api/generated.ts",
      client: "react-query",
      httpClient: "fetch",
      baseUrl: "",
      prettier: true,
      override: {
        fetch: { includeHttpResponseReturnType: false },
        mutator: { path: "./src/api/fetchOrThrow.ts", name: "fetchOrThrow" },
      },
    },
  },
});
