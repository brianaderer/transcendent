import { type RequestHandler } from "msw";
import { setupServer } from "msw/node";

/**
 * A stand-in backend for one test file (CLAUDE.md §7: tests never reach a real server).
 * The app asks for relative addresses like /api/days; Node's fetch needs whole ones, so
 * they are resolved against the test page's address first.
 */
export function standInBackend(...handlers: RequestHandler[]) {
  const server = setupServer(...handlers);
  const withoutShim = globalThis.fetch;
  beforeAll(() => {
    server.listen({ onUnhandledRequest: "error" });
    const intercepted = globalThis.fetch; // the stand-in only sees requests made after listen()
    globalThis.fetch = (input, init) =>
      intercepted(typeof input === "string" ? new URL(input, location.origin) : input, init);
  });
  afterEach(() => server.resetHandlers());
  afterAll(() => {
    server.close();
    globalThis.fetch = withoutShim;
  });
  return server;
}
