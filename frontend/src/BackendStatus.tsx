import { useQuery } from "@tanstack/react-query";

import { describeHealth, fetchHealth } from "./health";

const HEALTH_REFRESH_MILLISECONDS = 5000;

export function BackendStatus() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: HEALTH_REFRESH_MILLISECONDS,
  });

  if (health.isPending) return <p>Checking the backend…</p>;
  if (health.isError) return <p>Backend unreachable</p>;
  return <p>{describeHealth(health.data)}</p>;
}
