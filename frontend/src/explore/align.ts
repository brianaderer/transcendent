/**
 * Lines a new map up with the one before it (atlas plate 31, "Gliding"): every new map is
 * turned, flipped if that fits better, scaled and moved to best match the old one on the
 * posts both share, so a staying dot moves only as far as the map really changed.
 */

export type Place = { id: string; x: number; y: number };
type Point = { x: number; y: number };
type Pair = readonly [old: Place, now: Place];
type Carry = (place: Place) => Point;

const FEWEST_SHARED = 3; // with fewer shared posts there's nothing to line up against

export function alignTo<T extends Place>(previous: Place[], next: T[]): T[] {
  const before = new Map(previous.map((place) => [place.id, place]));
  const pairs = next
    .filter((place) => before.has(place.id))
    .map((place) => [before.get(place.id)!, place] as const);
  if (pairs.length < FEWEST_SHARED) return next;
  const carry = [false, true]
    .map((flip) => carryFor(pairs, flip))
    .reduce((best, candidate) =>
      squaredError(pairs, candidate) < squaredError(pairs, best) ? candidate : best,
    );
  return next.map((place) => ({ ...place, ...carry(place) }));
}

/** The turn and scale (after a flip, if asked) that best carries the new places onto the old. */
function carryFor(pairs: readonly Pair[], flip: boolean): Carry {
  const mirroredPairs = pairs.map(([old, now]) => [old, mirrored(now, flip)] as const);
  const { angle, scale, oldCentre, newCentre } = fitTurnAndScale(mirroredPairs);
  return (place) => {
    const { x, y } = mirrored(place, flip);
    const [dx, dy] = [x - newCentre.x, y - newCentre.y];
    return {
      x: oldCentre.x + scale * (dx * Math.cos(angle) - dy * Math.sin(angle)),
      y: oldCentre.y + scale * (dx * Math.sin(angle) + dy * Math.cos(angle)),
    };
  };
}

function mirrored<T extends Point>(place: T, flip: boolean): T {
  return flip ? { ...place, y: -place.y } : place;
}

/** The least-squares turn and scale between two sets of matched points (Procrustes in 2D). */
function fitTurnAndScale(pairs: readonly (readonly [Point, Point])[]) {
  const oldCentre = centre(pairs.map(([old]) => old));
  const newCentre = centre(pairs.map(([, now]) => now));
  let dot = 0;
  let cross = 0;
  let spread = 0;
  for (const [old, now] of pairs) {
    const [ax, ay] = [old.x - oldCentre.x, old.y - oldCentre.y];
    const [bx, by] = [now.x - newCentre.x, now.y - newCentre.y];
    dot += ax * bx + ay * by;
    cross += bx * ay - by * ax;
    spread += bx * bx + by * by;
  }
  const scale = spread ? Math.hypot(dot, cross) / spread : 1;
  return { angle: Math.atan2(cross, dot), scale, oldCentre, newCentre };
}

function squaredError(pairs: readonly Pair[], carry: Carry): number {
  return pairs.reduce((sum, [old, now]) => {
    const placed = carry(now);
    return sum + (placed.x - old.x) ** 2 + (placed.y - old.y) ** 2;
  }, 0);
}

function centre(points: Point[]): Point {
  const x = points.reduce((sum, point) => sum + point.x, 0) / points.length;
  const y = points.reduce((sum, point) => sum + point.y, 0) / points.length;
  return { x, y };
}
