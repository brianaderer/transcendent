import { useQuery } from "@tanstack/react-query";

import { fetchHealth, servicesDown } from "./health";

export function BackendStatus() {
  const health = useQuery({ queryKey: ["health"], queryFn: fetchHealth, refetchInterval: 5000 });

  if (health.isPending) return <p>Checking the backend…</p>;
  if (health.isError) return <p>Backend unreachable</p>;
  const down = servicesDown(health.data);
  return <p>{down.length ? `Not answering: ${down.join(", ")}` : "Backend running"}</p>;
}
