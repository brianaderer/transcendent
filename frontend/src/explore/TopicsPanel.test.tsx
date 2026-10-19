import { fireEvent, render, screen } from "@testing-library/react";

import type { TopicInRange } from "../api/generated";
import { renderInRouter } from "../test/renderInRouter";
import { Sparkline, TopicsPanel } from "./TopicsPanel";
import { useUiState } from "./uiState";

const TOPIC: TopicInRange = {
  id: 3,
  label: "Anchoring",
  description: "d",
  first_seen: "2026-09-01",
  engagement: 5,
  posts: 2,
  daily: [1, 4],
  direction: "steady",
};

beforeEach(() => useUiState.setState({ highlightedTopic: null }));

test("a range with no topics says so", async () => {
  await renderInRouter(<TopicsPanel topics={[]} colours={new Map()} />);

  expect(screen.getByText("No topics in these days.")).toBeInTheDocument();
});

test("keyboard focus on a topic highlights it, as the pointer does, and leaving clears it", async () => {
  await renderInRouter(<TopicsPanel topics={[TOPIC]} colours={new Map()} />);
  const row = screen.getByText("Anchoring").closest("li")!;

  fireEvent.focus(row);
  expect(useUiState.getState().highlightedTopic).toBe(3);
  fireEvent.blur(row);
  expect(useUiState.getState().highlightedTopic).toBeNull();
});

test("a topic's name opens its detail page with the range in the address", async () => {
  await renderInRouter(
    <TopicsPanel topics={[TOPIC]} colours={new Map()} />,
    "/?start=2026-10-12&end=2026-10-18",
  );

  const link = screen.getByRole("link", { name: "Anchoring" });
  expect(link).toHaveAttribute("href", "/topics/3?start=2026-10-12&end=2026-10-18");
});

function drawnPoints(values: number[]): string {
  const { container } = render(<Sparkline values={values} />);
  return container.querySelector("polyline")!.getAttribute("points")!;
}

test("a one-day sparkline is a single point at the start", () => {
  expect(drawnPoints([5])).toBe("0,0");
});

test("a sparkline of quiet days lies along the bottom, inside its box", () => {
  expect(drawnPoints([0, 0, 0])).toBe("0,16 30,16 60,16");
});
