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

test("each version's bar moves as its live events arrive", async () => {
  await showProgress();
  const bars = () => screen.getAllByRole("progressbar");
  expect(bars().map((bar) => bar.getAttribute("aria-valuenow"))).toEqual(["0", "0"]);

  act(() => {
    announce({ type: "step.started", version: "B", phase: "write" });
    announce({ type: "tool.called", version: "B", phase: "write", tool: "search", arguments: {} });
  });

  const [a, b] = bars();
  expect(a.getAttribute("aria-valuenow")).toBe("0");
  expect(Number(b.getAttribute("aria-valuenow"))).toBeGreaterThan(0);
  expect(screen.getByText("Writing the report · 1 tool call")).toBeInTheDocument();
});

test("once both versions are done, the panel says it is scoring them", async () => {
  await showProgress();

  act(() => {
    announce({ type: "step.finished", version: "A", phase: "predict", seconds: 7 });
    announce({ type: "step.finished", version: "B", phase: "predict", seconds: 9 });
  });

  expect(await screen.findByText("Scoring both versions…")).toBeInTheDocument();
});

const SOONER_THAN_THE_NEXT_STATE_CHECK_MS = 1000; // the panel rereads the run every 3 s anyway

test("the links appear as soon as the run says it has finished, without waiting to check", async () => {
  await showProgress();
  await screen.findByRole("region", { name: "Report progress" });
  runState = FINISHED_RUN;

  act(() => announce({ type: "run.finished" }));

  expect(await screen.findByText("See the comparison", {}, { timeout: SOONER_THAN_THE_NEXT_STATE_CHECK_MS })).toBeInTheDocument();
});
