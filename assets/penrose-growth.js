import { asFive, latticeKey } from "./cyclotomic-five.js";
import { solveAmmannDecorations } from "./penrose-ammann.js?v=20260907-settings";

const mod5 = n => (n % 5 + 5) % 5;
const sign = (a, b) => {
  if (!b) return a < 0n ? -1 : a > 0n ? 1 : 0;
  if (!a) return b < 0n ? -1 : 1;
  if ((a > 0n) === (b > 0n)) return a > 0n ? 1 : -1;
  const d = a * a - 5n * b * b;
  return a > 0n ? (d > 0n ? 1 : -1) : (d > 0n ? -1 : 1);
};
const compare = (a, b) => sign(a[0] - b[0], a[1] - b[1]);
const sine = [[0n, 0n], [2n, 0n], [-1n, 1n], [1n, -1n], [-2n, 0n]];
export function orientation(a, b, c) {
  const u = b.coeff.map((n, i) => BigInt(n - a.coeff[i]));
  const v = c.coeff.map((n, i) => BigInt(n - a.coeff[i]));
  let x = 0n, y = 0n;
  for (let i = 0; i < 5; i++) for (let j = 0; j < 5; j++) {
    const factor = u[i] * v[j], [p, q] = sine[mod5(j - i)]; x += factor * p; y += factor * q;
  }
  return sign(x, y);
}
const geometry = new WeakMap();
const data = tile => {
  if (geometry.has(tile)) return geometry.get(tile);
  const bounds = [0, 1].map(axis => {
    const values = tile.exactPoints.map(p => p.coeff.reduce(([x, y], n, i) => {
      const sep = Math.min(mod5(i - axis), mod5(axis - i));
      return [x + BigInt(n) * (sep === 0 ? 4n : -1n), y + BigInt(n) * (sep === 0 ? 0n : sep === 1 ? 1n : -1n)];
    }, [0n, 0n]));
    values.sort(compare); return [values[0], values.at(-1)];
  });
  const value = { bounds, winding: orientation(...tile.exactPoints.slice(0, 3)) };
  geometry.set(tile, value); return value;
};
// Exact separating-axis test for convex rhombs. Edge/vertex contact is legal;
// crossing, containment and collinear interior overlap are all rejected.
export function interiorsOverlap(a, b) {
  if (data(a).bounds.some(([lo, hi], axis) => compare(hi, data(b).bounds[axis][0]) <= 0 || compare(data(b).bounds[axis][1], lo) <= 0)) return false;
  for (const [p, q] of [[a, b], [b, a]]) {
    for (let k = 0; k < 4; k++) if (q.exactPoints.every(v => data(p).winding * orientation(p.exactPoints[k], p.exactPoints[(k + 1) % 4], v) <= 0)) return false;
  }
  return true;
}
export function growthRhomb(base, i, j) {
  const coeffs = [base, base.map((n, k) => n + Number(k === i)), base.map((n, k) => n + Number(k === i || k === j)), base.map((n, k) => n + Number(k === j))];
  const exactPoints = coeffs.map(coeff => asFive({ coeff, denominator: 1 }));
  const vertices = exactPoints.map(latticeKey), w = Math.min(j - i, 5 - j + i) === 1 ? 2 : 4;
  return { id: [...vertices].sort().join("|"), vertices, exactPoints, weights: [w, 5 - w, w, 5 - w], kind: w === 2 ? "thick" : "thin",
    families: [i, j], edgeFamilies: [i, j, i, j], edgeSigns: [1, 1, -1, -1], presentation: "P3" };
}
const edgeKey = (t, k) => [t.vertices[k], t.vertices[(k + 1) % 4]].sort().join("|");
const edgeDistance = (t, k) => {
  const c = t.exactPoints[k].coeff.map((n, i) => BigInt(n + t.exactPoints[(k + 1) % 4].coeff[i]));
  let a = 4n * c.reduce((s, n) => s + n * n, 0n), b = 0n;
  for (let i = 0; i < 5; i++) for (let j = i + 1; j < 5; j++) {
    const n = 2n * c[i] * c[j]; a -= n;
    b += Math.min(j - i, 5 - j + i) === 1 ? n : -n;
  }
  return [a, b];
};
const priority = (key, seed) => { let h = (2166136261 ^ seed) >>> 0; for (const c of key) h = Math.imul(h ^ c.charCodeAt(0), 16777619) >>> 0; return h; };

export function createPenroseGrowth({ useMarkings = true, markingDirections = 5, targetCount = 60, nodeLimit = 10000, seed = 1 } = {}) {
  if (![targetCount, nodeLimit, seed].every(Number.isSafeInteger) || targetCount < 1 || targetCount > 420 || nodeLimit < 1 || nodeLimit > 100000) throw new RangeError("Invalid search budget");
  if (!Number.isInteger(markingDirections) || markingDirections < 1 || markingDirections > 5) throw new RangeError("Marking direction count must be 1–5");
  const active = [], edges = new Map(), totals = new Map(), ids = new Set(), candidatesCache = new Map();
  const stats = { proposals: 0, capacityPrunes: 0, geometryPrunes: 0, topologyPrunes: 0, markingPrunes: 0, backtracks: 0, peak: 1 };
  let status = "ready", marking = null, lastEvent = null;
  const put = tile => {
    active.push(tile); ids.add(tile.id);
    tile.vertices.forEach((v, k) => totals.set(v, (totals.get(v) || 0) + tile.weights[k]));
    for (let k = 0; k < 4; k++) {
      const key = edgeKey(tile, k); if (!edges.has(key)) edges.set(key, []);
      edges.get(key).push({ tile, k, key, distance: edgeDistance(tile, k) });
    }
  };
  const remove = tile => {
    active.pop(); ids.delete(tile.id);
    tile.vertices.forEach((v, k) => { const n = totals.get(v) - tile.weights[k]; if (n) totals.set(v, n); else totals.delete(v); });
    for (let k = 0; k < 4; k++) { const key = edgeKey(tile, k); edges.get(key).pop(); if (!edges.get(key).length) edges.delete(key); }
  };
  const singleBoundary = () => {
    const graph = new Map();
    for (const records of edges.values()) if (records.length === 1) {
      const { tile, k } = records[0], a = tile.vertices[k], b = tile.vertices[(k + 1) % 4];
      if (!graph.has(a)) graph.set(a, []); if (!graph.has(b)) graph.set(b, []);
      graph.get(a).push(b); graph.get(b).push(a);
    }
    if (!graph.size || [...graph.values()].some(n => n.length !== 2)) return false;
    const seen = new Set(), queue = [graph.keys().next().value];
    while (queue.length) { const v = queue.pop(); if (seen.has(v)) continue; seen.add(v); queue.push(...graph.get(v)); }
    return seen.size === graph.size;
  };
  const candidates = edge => {
    if (candidatesCache.has(edge.key)) return candidatesCache.get(edge.key);
    const { tile, k } = edge, family = tile.edgeFamilies[k];
    const low = tile.exactPoints[tile.edgeSigns[k] > 0 ? k : (k + 1) % 4].coeff;
    const result = [];
    for (let other = 0; other < 5; other++) if (other !== family) for (const side of [0, 1]) {
      result.push(growthRhomb(low.map((n, i) => n - (i === other ? side : 0)), Math.min(family, other), Math.max(family, other)));
    }
    result.sort((a, b) => priority(a.id, seed) - priority(b.id, seed) || a.id.localeCompare(b.id));
    candidatesCache.set(edge.key, result); return result;
  };
  function* search() {
    if (active.length >= targetCount) { status = "target reached"; return true; }
    if (stats.proposals >= nodeLimit) { status = "budget reached"; return false; }
    const frontier = [...edges.values()].filter(r => r.length === 1).map(r => r[0]);
    frontier.sort((a, b) => compare(a.distance, b.distance) || a.key.localeCompare(b.key));
    const edge = frontier[0];
    if (!edge) return false;
    for (const tile of candidates(edge)) {
      if (ids.has(tile.id)) continue;
      if (stats.proposals >= nodeLimit) { status = "budget reached"; return false; }
      stats.proposals++;
      yield { type: "try", tile, message: "Try a lattice rhomb on the nearest exposed edge" };
      if (tile.vertices.some((v, k) => (totals.get(v) || 0) + tile.weights[k] > 10)) {
        stats.capacityPrunes++; yield { type: "reject", tile, message: "Corner capacity exceeds ten" }; continue;
      }
      if (active.some(other => interiorsOverlap(tile, other))) {
        stats.geometryPrunes++; yield { type: "reject", tile, message: "Exact polygon overlap" }; continue;
      }
      const before = marking;
      const next = useMarkings ? solveAmmannDecorations([...active, tile], { directionCount: markingDirections }) : null;
      if (next && !next.success) { stats.markingPrunes++; yield { type: "reject", tile, message: "Fixed Ammann stripes cannot match" }; continue; }
      put(tile);
      if (!singleBoundary()) {
        remove(tile); stats.topologyPrunes++; yield { type: "reject", tile, message: "Placement would close a hole or pinch the boundary" }; continue;
      }
      marking = next; stats.peak = Math.max(stats.peak, active.length);
      yield { type: "add", tile, message: "Place rhomb" };
      if (yield* search()) return true;
      if (status === "budget reached") return false;
      remove(tile); marking = before; stats.backtracks++;
      yield { type: "remove", tile, message: "Backtrack from an exhausted frontier" };
    }
    return false;
  }
  function* run() {
    const tile = growthRhomb([0, 0, 0, 0, 0], 0, 1); put(tile);
    if (useMarkings) marking = solveAmmannDecorations(active, { directionCount: markingDirections });
    status = "searching";
    yield { type: "add", tile, message: "Same thick-rhomb seed in both searches" };
    if (!(yield* search()) && status !== "budget reached") status = "frontier exhausted";
  }
  const iterator = run();
  return {
    next() { const step = iterator.next(); if (step.value) lastEvent = step.value; return step; },
    snapshot() { return { tiles: [...active], orientations: marking ? [...marking.orientationByTile] : [], stats: { ...stats }, status, event: lastEvent, useMarkings, markingDirections }; }
  };
}
