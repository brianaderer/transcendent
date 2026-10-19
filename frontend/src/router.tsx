import { createRootRoute, createRoute, createRouter, Outlet } from "@tanstack/react-router";

import { ExplorePage } from "./explore/ExplorePage";
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
  validateSearch: (search: Record<string, unknown>): Partial<DayRange> => ({
    start: typeof search.start === "string" ? search.start : undefined,
    end: typeof search.end === "string" ? search.end : undefined,
  }),
  component: ExplorePage,
});

export function buildRouter(history?: Parameters<typeof createRouter>[0]["history"]) {
  return createRouter({ routeTree: root.addChildren([explore]), history });
}

declare module "@tanstack/react-router" {
  interface Register {
    router: ReturnType<typeof buildRouter>;
  }
}
