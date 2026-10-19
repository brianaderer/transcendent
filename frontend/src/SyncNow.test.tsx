import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitForElementToBeRemoved } from "@testing-library/react";
import { http, HttpResponse } from "msw";

import { IngestionStatus } from "./IngestionStatus";
import { standInBackend } from "./test/standInBackend";

const UP_TO_DATE = {
  days_done: 56,
  days_wanted: 56,
  posts: 9412,
  latest_day: "2026-10-18",
  running_day: null,
  failed_day: null,
  failed_reason: null,
  backfill: null,
};
const SYNC_ANSWER = {
  queued: true,
  reason: "days_missing",
  missing_days: ["2026-10-19"],
  next_complete_day: "2026-10-20",
  next_complete_at: "2026-10-21T06:00:00Z",
};
let status: object;
let syncsAsked: number;

standInBackend(
  http.get("*/api/ingestion", () => HttpResponse.json(status)),
  http.post("*/api/catch-up", () => {
    syncsAsked += 1;
    return HttpResponse.json(SYNC_ANSWER);
  }),
);

class SilentEventSource {
  onmessage = null;
  close() {}
}

beforeEach(() => {
  vi.stubGlobal("EventSource", SilentEventSource);
  status = UP_TO_DATE;
  syncsAsked = 0;
});
afterEach(() => vi.unstubAllGlobals());

function renderStatus(answerShownMs?: number) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <IngestionStatus answerShownMs={answerShownMs} />
    </QueryClientProvider>,
  );
}

async function syncButton() {
  return screen.findByRole("button", { name: "Sync now" });
}

test("asks for a catch-up and says which day it will fetch", async () => {
  renderStatus();

  fireEvent.click(await syncButton());

  expect(await screen.findByText("Fetching 19 Oct…")).toBeInTheDocument();
  expect(syncsAsked).toBe(1);
});

test("the answer shows briefly, then goes", async () => {
  renderStatus(50);

  fireEvent.click(await syncButton());

  await waitForElementToBeRemoved(await screen.findByText("Fetching 19 Oct…"));
});

test("can't be pressed while a day is loading", async () => {
  status = { ...UP_TO_DATE, running_day: "2026-10-19" };
  renderStatus();

  expect(await syncButton()).toBeDisabled();
});

test("can't be pressed while the seed's history is being prepared", async () => {
  status = { ...UP_TO_DATE, days_done: 0, backfill: { what: "posts", done: 1, total: 9 } };
  renderStatus();

  expect(await syncButton()).toBeDisabled();
});
