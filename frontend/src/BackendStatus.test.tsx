import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";

import { BackendStatus } from "./BackendStatus";

function renderWithHealth(body: unknown, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(JSON.stringify(body), { status })),
  );
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <BackendStatus />
    </QueryClientProvider>,
  );
}

afterEach(() => vi.unstubAllGlobals());

test("says the backend is running when every check passes", async () => {
  renderWithHealth({ status: "ok", checks: { database: true, queue: true } });

  expect(await screen.findByText("Backend running")).toBeInTheDocument();
});

test("names each service that isn't answering", async () => {
  renderWithHealth({ status: "degraded", checks: { database: true, queue: false } }, 503);

  expect(await screen.findByText("Not answering: queue")).toBeInTheDocument();
});
