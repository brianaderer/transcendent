import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryHistory, RouterProvider } from "@tanstack/react-router";
import { act, render, screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";

import { buildRouter } from "../router";
import { standInBackend } from "../test/standInBackend";
import { FINISHED_RUN } from "./fixtures";

let runState: object = FINISHED_RUN;

standInBackend(
  http.get("*/api/runs/0123456789ab", () => HttpResponse.json(runState)),
  http.get("*/api/runs/:other", () => HttpResponse.json({ detail: "no run" }, { status: 404 })),
  http.get("*/api/health", () => HttpResponse.json({ status: "ok", checks: {} })),
  http.get("*/api/ingestion", () =>
    HttpResponse.json({ days_done: 56, days_wanted: 56, posts: 1, latest_day: "2026-10-18" }),
  ),
);

class QuietEventSource {
  onmessage = null;
  close() {}
}

beforeEach(() => {
  runState = FINISHED_RUN;
  vi.stubGlobal("EventSource", QuietEventSource);
});
afterEach(() => vi.unstubAllGlobals());

function open(address: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={buildRouter(createMemoryHistory({ initialEntries: [address] }))} />
    </QueryClientProvider>,
  );
}

test("the document shows version B by default, with its topics beside it", async () => {
  open("/runs/0123456789ab/report");

  expect(await screen.findByText("Version B on winterizing.")).toBeInTheDocument();
  expect(screen.getByText("Written with retrieval", { exact: false })).toBeInTheDocument();
  expect(screen.getByText("1. Winterizing")).toBeInTheDocument();
});

test("version A's document can be read on its own", async () => {
  open("/runs/0123456789ab/report?version=A");

  expect(await screen.findByText("Version A on winterizing.")).toBeInTheDocument();
});

test("the comparison grids the real topics against both reports and marks invented ones", async () => {
  open("/runs/0123456789ab/comparison");

  const grid = await screen.findByRole("table", { name: /real topics/ });
  const winterizing = within(grid).getByText("1. Winterizing").closest("tr")!;
  expect(within(winterizing).getByText("#1, steady")).toBeInTheDocument();
  expect(within(winterizing).getByText("#1, rising")).toBeInTheDocument();
  expect(within(grid).getByText("Safety at sea")).toBeInTheDocument();
  expect(
    within(screen.getByRole("table", { name: "Scores" })).getByText("8 of 10"),
  ).toBeInTheDocument();
});

test("a run that isn't finished, or has gone, says so", async () => {
  runState = { state: "running", result: null, reason: null };
  open("/runs/0123456789ab/comparison");
  expect(await screen.findByText("The run is still going…")).toBeInTheDocument();
});

test("a run older than a day is explained", async () => {
  open("/runs/ffffffffffff/report");

  expect(await screen.findByText(/kept for a day/)).toBeInTheDocument();
  await act(async () => {});
});
