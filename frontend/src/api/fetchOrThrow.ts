/**
 * Every generated API call goes through here (orval's mutator, see orval.config.ts): an
 * answer that isn't a success is thrown, so React Query reports it as an error instead of
 * handing the page an error's body as if it were data.
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: unknown,
  ) {
    super(`The API answered ${status}`);
  }
}

export async function fetchOrThrow<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  const body = await readBody(response);
  if (!response.ok) throw new ApiError(response.status, body);
  return body as T;
}

const NO_BODY = [204, 205, 304];

async function readBody(response: Response): Promise<unknown> {
  if (NO_BODY.includes(response.status)) return null;
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}
