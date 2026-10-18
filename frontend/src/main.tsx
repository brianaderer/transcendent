import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { BackendStatus } from "./BackendStatus";
import { IngestionStatus } from "./IngestionStatus";

const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <h1>Community Voices</h1>
      <BackendStatus />
      <IngestionStatus />
    </QueryClientProvider>
  </StrictMode>,
);
