export type Health = { status: "ok" | "degraded"; checks: Record<string, boolean> };

/** The backend answers 503 with the same body when something is down, so read it either way. */
export async function fetchHealth(): Promise<Health> {
  const response = await fetch("/api/health");
  return (await response.json()) as Health;
}

export function describeHealth(health: Health): string {
  const down = servicesDown(health);
  return down.length ? `Not answering: ${down.join(", ")}` : "Backend running";
}

function servicesDown(health: Health): string[] {
  return Object.entries(health.checks)
    .filter(([, answering]) => !answering)
    .map(([service]) => service);
}
