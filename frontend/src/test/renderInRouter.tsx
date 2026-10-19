import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

/**
 * Renders a part that holds links on a page of its own, since a link needs a router; the
 * address is `address`, so a part that reads the range from it finds one. Resolves once
 * the part is on screen.
 */
export async function renderInRouter(part: ReactNode, address = "/") {
  const root = createRootRoute({ component: () => <div data-testid="rendered">{part}</div> });
  const router = createRouter({
    routeTree: root,
    history: createMemoryHistory({ initialEntries: [address] }),
  });
  render(<RouterProvider router={router} />);
  await screen.findByTestId("rendered");
  return router;
}
