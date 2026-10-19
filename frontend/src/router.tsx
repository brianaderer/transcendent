import { createRootRoute, createRoute, createRouter, Outlet } from "@tanstack/react-router";

import { ExplorePage } from "./explore/ExplorePage";
import { ComparisonPage } from "./runs/ComparisonPage";
import { ReportPage } from "./runs/ReportPage";
import type { DayRange } from "./explore/range";
import { TopBar } from "./TopBar";

const root = createRootRoute({
  component: () => (
    <div className="min-h-screen bg-stone-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <TopBar />
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  ),
});

/** The range lives in the address, so a reviewer can share exactly what they see. */
const explore = createRoute({
  getParentRoute: () => root,
  path: "/",
  validateSearch: (search: Record<string, unknown>): ExploreSearch => ({
    start: text(search.start),
    end: text(search.end),
    run: text(search.run),
  }),
  component: ExplorePage,
});

/** A run's results are linked by its id; they are kept for a day (atlas OPEN-24). */
const report = createRoute({
  getParentRoute: () => root,
  path: "/runs/$runId/report",
  validateSearch: (search: Record<string, unknown>): { version?: "A" | "B" } => ({
    version: search.version === "A" || search.version === "B" ? search.version : undefined,
  }),
  component: ReportPage,
});

const comparison = createRoute({
  getParentRoute: () => root,
  path: "/runs/$runId/comparison",
  component: ComparisonPage,
});

/** Explore's address: its range, and the run it started, if any. */
export type ExploreSearch = Partial<DayRange> & { run?: string };

function text(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

export function buildRouter(history?: Parameters<typeof createRouter>[0]["history"]) {
  return createRouter({ routeTree: root.addChildren([explore, report, comparison]), history });
}

declare module "@tanstack/react-router" {
  interface Register {
    router: ReturnType<typeof buildRouter>;
  }
}
