import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen } from "@testing-library/react";

import { IngestionStatus } from "./IngestionStatus";

class FakeEventSource {
  static latest: FakeEventSource;
  onmessage: ((event: MessageEvent) => void) | null = null;
  constructor(public url: string) {
    FakeEventSource.latest = this;
  }
  close() {}
  send(data: object) {
    this.onmessage?.(new MessageEvent("message", { data: JSON.stringify(data) }));
  }
}

function serveStatus(daysDone: () => number) {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            days_done: daysDone(),
            days_wanted: 56,
            posts: daysDone() * 500,
            latest_day: null,
            running_day: "2026-08-25",
            failed_day: null,
            failed_reason: null,
          }),
        ),
    ),
  );
}

afterEach(() => vi.unstubAllGlobals());

test("updates the progress when a live event says a day finished", async () => {
  let daysDone = 2;
  serveStatus(() => daysDone);
  vi.stubGlobal("EventSource", FakeEventSource);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <IngestionStatus />
    </QueryClientProvider>,
  );
  expect(await screen.findByText(/2 of 56 days/)).toBeInTheDocument();

  daysDone = 3;
  act(() => FakeEventSource.latest.send({ type: "day.finished", day: "2026-08-25" }));

  expect(await screen.findByText(/3 of 56 days/)).toBeInTheDocument();
  expect(FakeEventSource.latest.url).toBe("/api/streams/ingestion/events");
});
