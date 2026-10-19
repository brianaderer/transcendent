import { alignTo, type Place } from "./align";

const BEFORE: Place[] = [
  { id: "a", x: 0, y: 0 },
  { id: "b", x: 1, y: 0 },
  { id: "c", x: 0, y: 1 },
  { id: "d", x: 1, y: 1 },
];

function turned(places: Place[], angle: number, scale: number, flip = false): Place[] {
  return places.map(({ id, x, y }) => {
    const flippedY = flip ? -y : y;
    return {
      id,
      x: scale * (x * Math.cos(angle) - flippedY * Math.sin(angle)) + 5,
      y: scale * (x * Math.sin(angle) + flippedY * Math.cos(angle)) - 3,
    };
  });
}

function expectClose(actual: Place[], expected: Place[]) {
  actual.forEach((place, n) => {
    expect(place.x).toBeCloseTo(expected[n].x);
    expect(place.y).toBeCloseTo(expected[n].y);
  });
}

test("a map that came out turned, scaled and moved is put back where it was", () => {
  expectClose(alignTo(BEFORE, turned(BEFORE, 2, 3)), BEFORE);
});

test("a map that came out mirrored is flipped back", () => {
  expectClose(alignTo(BEFORE, turned(BEFORE, 0.5, 1, true)), BEFORE);
});

test("a new post is carried along with the rest", () => {
  const next = turned([...BEFORE, { id: "e", x: 2, y: 2 }], 1, 2);

  expectClose(alignTo(BEFORE, next).slice(4), [{ id: "e", x: 2, y: 2 }]);
});

test("with too few posts in common the new map is left as it is", () => {
  const next = turned(BEFORE.slice(0, 2), 1, 2);

  expect(alignTo(BEFORE, next)).toEqual(next);
  expect(alignTo([], BEFORE)).toEqual(BEFORE);
});
