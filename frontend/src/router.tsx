import { createRootRoute, createRoute, createRouter, Outlet } from "@tanstack/react-router";

import { ExplorePage } from "./explore/ExplorePage";
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
  validateSearch: rangeInAddress,
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

/** The range in the address; anything that isn't text is dropped. */
export function rangeInAddress(search: Record<string, unknown>): Partial<DayRange> {
  return {
    start: typeof search.start === "string" ? search.start : undefined,
    end: typeof search.end === "string" ? search.end : undefined,
  };
}

export function buildRouter(history?: Parameters<typeof createRouter>[0]["history"]) {
  return createRouter({ routeTree: root.addChildren([explore, topic, retrievals]), history });
}

declare module "@tanstack/react-router" {
  interface Register {
    router: ReturnType<typeof buildRouter>;
  }
}
