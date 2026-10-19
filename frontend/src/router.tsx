import { createRootRoute, createRoute, createRouter, Outlet } from "@tanstack/react-router";

import { ExplorePage } from "./explore/ExplorePage";
import { ComparisonPage } from "./runs/ComparisonPage";
import { ReportPage } from "./runs/ReportPage";
import type { DayRange } from "./explore/range";
import { RetrievalsPage } from "./retrievals/RetrievalsPage";
import { type RetrievalSearch, retrievalSearch } from "./retrievals/search";
import { TopBar } from "./TopBar";
import { TopicPage } from "./topic/TopicPage";

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
    ...rangeInAddress(search),
    run: text(search.run),
  }),
  component: ExplorePage,
});

/** Every other screen keeps the range chosen on Explore (atlas plate 31, global layout). */
const topic = createRoute({
  getParentRoute: () => root,
  path: "/topics/$topicId",
  validateSearch: rangeInAddress,
  component: TopicPage,
});

const retrievals = createRoute({
  getParentRoute: () => root,
  path: "/retrievals",
  validateSearch: (search: Record<string, unknown>): RetrievalSearch => ({
    ...rangeInAddress(search),
    ...retrievalSearch(search),
  }),
  component: RetrievalsPage,
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

/** The range in the address; anything that isn't text is dropped. */
export function rangeInAddress(search: Record<string, unknown>): Partial<DayRange> {
  return { start: text(search.start), end: text(search.end) };
}

function text(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

export function buildRouter(history?: Parameters<typeof createRouter>[0]["history"]) {
  const routes = [explore, topic, retrievals, report, comparison];
  return createRouter({ routeTree: root.addChildren(routes), history });
}

declare module "@tanstack/react-router" {
  interface Register {
    router: ReturnType<typeof buildRouter>;
  }
}
