import { ApiError, fetchOrThrow } from "./fetchOrThrow";

function answering(status: number, body: string) {
  vi.stubGlobal("fetch", async () => new Response(body || null, { status }));
}

afterEach(() => vi.unstubAllGlobals());

test("a success is its body, read as JSON", async () => {
  answering(200, '{"id": 1}');

  expect(await fetchOrThrow("/api/topics/1")).toEqual({ id: 1 });
});

test("an answer that isn't a success is thrown with its status and body", async () => {
  answering(404, '{"detail": "no topic with id 2"}');

  const error = await fetchOrThrow("/api/topics/2").catch((thrown) => thrown);

  expect(error).toBeInstanceOf(ApiError);
  expect(error).toMatchObject({ status: 404, detail: { detail: "no topic with id 2" } });
});

test("an empty success is null", async () => {
  answering(204, "");

  expect(await fetchOrThrow("/api/nothing")).toBeNull();
});
