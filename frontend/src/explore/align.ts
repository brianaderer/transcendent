/**
 * Lines a new map up with the one before it (atlas plate 31, "Gliding"): every new map is
 * turned, flipped if that fits better, scaled and moved to best match the old one on the
 * posts both share, so a staying dot moves only as far as the map really changed.
 */

export type Place = { id: string; x: number; y: number };

const FEWEST_SHARED = 3; // with fewer shared posts there's nothing to line up against

export function alignTo<T extends Place>(previous: Place[], next: T[]): T[] {
  const before = new Map(previous.map((p) => [p.id, p]));
  const shared = next.filter((p) => before.has(p.id));
  if (shared.length < FEWEST_SHARED) return next;
  const pairs = shared.map((p) => [before.get(p.id)!, p] as const);
  const turn = [false, true]
    .map((flip) => bestTurn(pairs, flip))
    .sort((a, b) => a.error - b.error)[0];
  return next.map((p) => ({ ...p, ...turn.apply(p) }));
}

type Pair = readonly [Place, Place];
type Turn = { error: number; apply: (p: Place) => { x: number; y: number } };

/** The rotation and scale (after an optional flip) that best carries the new places onto the old. */
function bestTurn(pairs: readonly Pair[], flip: boolean): Turn {
  const flipped = pairs.map(([old, now]) => [old, flip ? { ...now, y: -now.y } : now] as const);
  const oldCentre = centre(flipped.map(([old]) => old));
  const newCentre = centre(flipped.map(([, now]) => now));
  let dot = 0;
  let cross = 0;
  let spread = 0;
  for (const [old, now] of flipped) {
    const [ax, ay] = [old.x - oldCentre.x, old.y - oldCentre.y];
    const [bx, by] = [now.x - newCentre.x, now.y - newCentre.y];
    dot += ax * bx + ay * by;
    cross += bx * ay - by * ax;
    spread += bx * bx + by * by;
  }
  const angle = Math.atan2(cross, dot);
  const scale = spread ? Math.hypot(dot, cross) / spread : 1;
  const apply = (p: Place) => {
    const x = p.x - newCentre.x;
    const y = (flip ? -p.y : p.y) - newCentre.y;
    return {
      x: oldCentre.x + scale * (x * Math.cos(angle) - y * Math.sin(angle)),
      y: oldCentre.y + scale * (x * Math.sin(angle) + y * Math.cos(angle)),
    };
  };
  const error = flipped.reduce((sum, [old, now]) => {
    const placed = apply(flip ? { ...now, y: -now.y } : now);
    return sum + (placed.x - old.x) ** 2 + (placed.y - old.y) ** 2;
  }, 0);
  return { error, apply };
}

function centre(places: Place[]): { x: number; y: number } {
  const x = places.reduce((sum, p) => sum + p.x, 0) / places.length;
  const y = places.reduce((sum, p) => sum + p.y, 0) / places.length;
  return { x, y };
}
