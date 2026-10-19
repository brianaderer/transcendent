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

function serveStatus(daysDone: () => number, backfill: () => object | null = () => null) {
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
            backfill: backfill(),
          }),
        ),
    ),
  );
}

afterEach(() => vi.unstubAllGlobals());

function renderStatus() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <IngestionStatus />
    </QueryClientProvider>,
  );
}

test("shows the history's preparation counting up, then the days once it is done", async () => {
  let backfill: object | null = { what: "posts", done: 256, total: 12682 };
  serveStatus(
    () => 3,
    () => backfill,
  );
  vi.stubGlobal("EventSource", FakeEventSource);
  renderStatus();
  expect(await screen.findByText("Preparing the history: 256 of 12,682 posts")).toBeInTheDocument();

  backfill = { what: "posts", done: 512, total: 12682 };
  act(() => FakeEventSource.latest.send({ type: "backfill.progress", what: "posts", done: 512 }));
  expect(await screen.findByText("Preparing the history: 512 of 12,682 posts")).toBeInTheDocument();

  backfill = null;
  act(() => FakeEventSource.latest.send({ type: "backfill.finished" }));
  expect(await screen.findByText(/3 of 56 days/)).toBeInTheDocument();
});

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
