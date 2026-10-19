import { colourOf, NO_TOPIC, OTHER_TOPIC, PALETTE, topicColours } from "./colours";

test("the twelve busiest topics get their own colours and the rest share one", () => {
  const colours = topicColours(Array.from({ length: 14 }, (_, n) => n + 1));

  expect(new Set([...colours.values()].slice(0, 12)).size).toBe(12);
  expect(colours.get(1)).toBe(PALETTE[0]);
  expect(colours.get(13)).toBe(OTHER_TOPIC);
});

test("a post whose thread has no topic yet is grey, and an unlisted topic is muted", () => {
  const colours = topicColours([7]);

  expect(colourOf(null, colours)).toBe(NO_TOPIC);
  expect(colourOf(99, colours)).toBe(OTHER_TOPIC);
});
