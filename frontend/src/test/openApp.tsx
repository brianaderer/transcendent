import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryHistory, RouterProvider } from "@tanstack/react-router";
import { render } from "@testing-library/react";

import { buildRouter } from "../router";

/** The whole app at an address, with the answers it fetches never retried. */
export function openApp(address: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = buildRouter(createMemoryHistory({ initialEntries: [address] }));
  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return router;
}

/** Live events that never arrive: for pages whose test isn't about them. */
export class SilentEventSource {
  onmessage: ((event: MessageEvent) => void) | null = null;
  constructor(public url: string) {}
  close() {}
}
