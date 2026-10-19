import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";

import { renderInRouter } from "../test/renderInRouter";
import { standInBackend } from "../test/standInBackend";
import { FINISHED_RUN } from "./fixtures";
import { RunProgress } from "./RunProgress";

const RUN_ID = "0123456789ab";
let runState: object;

standInBackend(http.get(`*/api/runs/${RUN_ID}`, () => HttpResponse.json(runState)));

class FakeEventSource {
  static opened: FakeEventSource[] = [];
  onmessage: ((event: MessageEvent) => void) | null = null;
  constructor(public url: string) {
    FakeEventSource.opened.push(this);
  }
  close() {}
}

function announce(event: object) {
  const data = JSON.stringify(event);
  for (const source of FakeEventSource.opened)
    source.onmessage?.(new MessageEvent("message", { data }));
}

beforeEach(() => {
  vi.stubGlobal("EventSource", FakeEventSource);
  FakeEventSource.opened = [];
  runState = { state: "running", result: null, reason: null };
});
afterEach(() => vi.unstubAllGlobals());

function showProgress() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return renderInRouter(
    <QueryClientProvider client={client}>
      <RunProgress runId={RUN_ID} />
    </QueryClientProvider>,
  );
}

test("listens on the run's own stream, named as the backend names it", async () => {
  await showProgress();

  expect(FakeEventSource.opened.map((s) => s.url)).toEqual([`/api/streams/run-${RUN_ID}/events`]);
});

test("a run.failed live event shows its reason", async () => {
  await showProgress();

  act(() => announce({ type: "run.failed", reason: "OPENROUTER_API_KEY is not set" }));

  expect(
    await screen.findByText("The run stopped: OPENROUTER_API_KEY is not set"),
  ).toBeInTheDocument();
});

test("a run read back as failed, with no live event, shows the stored reason", async () => {
  runState = { state: "failed", result: null, reason: "the model is unreachable" };

  await showProgress();

  expect(await screen.findByText("The run stopped: the model is unreachable")).toBeInTheDocument();
});

test("a finished run links to both results", async () => {
  runState = FINISHED_RUN;

  await showProgress();

  expect(await screen.findByRole("link", { name: "Read the report" })).toHaveAttribute(
    "href",
    `/runs/${RUN_ID}/report`,
  );
  expect(screen.getByRole("link", { name: "See the comparison" })).toHaveAttribute(
    "href",
    `/runs/${RUN_ID}/comparison`,
  );
});
