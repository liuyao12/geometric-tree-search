import { canonical, cycloAdd, cycloMultiply, edgePort, latticeKey, starMap } from "./cyclotomic-five.js";

const sub = (a, b) => cycloAdd(a, { ...canonical(b), coeff: canonical(b).coeff.map(n => -n) });
const conjugate = a => starMap(starMap(a));
const one = { coeff: [1, 0, 0, 0], denominator: 1 };
const complement = t => sub(one, t);
// Unit-edge normalization of the classical markings in Porrier & Fernique,
// Ammann Bars for Octagonal Tilings, Fig. 1 (arXiv:2205.13973v6).
// φ = -ζ²-ζ³; use exact lengths, not the rounded TikZ drawing coordinates.
const a = { coeff: [-1, 0, -1, -1], denominator: 4 }; // 1/(4φ)
const b = { coeff: [2, 0, 1, 1], denominator: 2 }; // 1/(2φ²)
const m = { coeff: [1, 0, 0, 0], denominator: 2 };
// Start at an acute corner and follow the tile's boundary. Each entry is one
// entire stripe, expressed as two (edge, parameter) endpoints. No stripe is
// optional, including on the boundary of a finite patch.
export const AMMANN_TEMPLATES = {
  thick: [ [[0, a], [3, m]], [[3, complement(a)], [0, m]],
    [[0, m], [1, b]], [[3, m], [2, complement(b)]], [[1, b], [2, complement(b)]] ],
  thin: [ [[0, m], [1, m]], [[0, m], [3, complement(b)]],
    [[1, m], [2, b]], [[0, a], [3, complement(b)]], [[1, complement(a)], [2, b]] ]
};
export function ammannPrototype(kind) {
  if (!AMMANN_TEMPLATES[kind]) throw new TypeError("Unknown rhomb kind");
  const j = kind === "thick" ? 1 : 2;
  const coeffs = [Array(5).fill(0), [1, 0, 0, 0, 0], Array.from({ length: 5 }, (_, k) => Number(k === 0 || k === j)), Array.from({ length: 5 }, (_, k) => Number(k === j))];
  return { id: `prototype:${kind}`, kind, exactPoints: coeffs.map(coeff => ({ coeff, denominator: 1 })),
    weights: kind === "thick" ? [2, 3, 2, 3] : [4, 1, 4, 1] };
}
const axes = Array.from({ length: 5 }, (_, i) => ({ coeff: Array.from({ length: 5 }, (_, k) => Number(i === k)), denominator: 1 }));
export const exactlyPerpendicular = (u, v) => cycloAdd(cycloMultiply(u, conjugate(v)), cycloMultiply(conjugate(u), v)).coeff.every(n => n === 0);
const cache = new WeakMap();
const edgeKey = (p, q) => [latticeKey(p), latticeKey(q)].sort().join("|");

export function ammannStates(tile) {
  if (cache.has(tile)) return cache.get(tile);
  if (!AMMANN_TEMPLATES[tile.kind] || tile.exactPoints.length !== 4) throw new TypeError("Ammann markings require P3 rhombs");
  const acute = Math.min(...tile.weights);
  const states = tile.weights.flatMap((weight, start) => {
    if (weight !== acute) return [];
    const points = Array.from({ length: 4 }, (_, k) => tile.exactPoints[(start + k) % 4]);
    const ports = new Map(points.map((p, k) => [edgeKey(p, points[(k + 1) % 4]), []]));
    const bars = AMMANN_TEMPLATES[tile.kind].map((pair, stripe) => {
      const ends = pair.map(([edge, parameter]) => ({
        edge: edgeKey(points[edge], points[(edge + 1) % 4]),
        point: edgePort(points[edge], points[(edge + 1) % 4], parameter)
      }));
      const from = ends[0].point, to = ends[1].point, delta = sub(to, from);
      const family = axes.findIndex(axis => exactlyPerpendicular(delta, axis));
      if (family < 0) throw new Error("A template stripe is not in an Ammann direction");
      for (const port of ends) ports.get(port.edge).push(`${latticeKey(port.point)}:${family}`);
      return { from, to, family, stripe, ends, tileId: tile.id, color: "#753c1b" };
    });
    const signatures = new Map([...ports].map(([edge, values]) => [edge, values.sort().join(";")]));
    return [{ start, bars, signatures }];
  });
  cache.set(tile, states);
  return states;
}

// Each tile has just two rigid orientations of ONE complete decorated
// prototile. Shared edges equate the complete port+direction multisets.
// Arc consistency propagates domains; DFS resolves remaining orientation
// choices. Nothing consults a window, a target tiling, or neighboring stripes
// to change the template itself.
// Partial direction sets are deliberately weaker diagnostic constraints.
// They never alter the five-stripe prototile itself.
export function ammannSignature(state, edge, directionCount = 5) {
  if (!Number.isInteger(directionCount) || directionCount < 1 || directionCount > 5) throw new RangeError("Marking direction count must be 1–5");
  const signature = state.signatures.get(edge);
  if (signature === undefined || directionCount === 5) return signature;
  return signature.split(";").filter(port => Number(port.slice(port.lastIndexOf(":") + 1)) < directionCount).join(";");
}

export function solveAmmannDecorations(tiles, { directionCount = 5 } = {}) {
  if (!Number.isInteger(directionCount) || directionCount < 1 || directionCount > 5) throw new RangeError("Marking direction count must be 1–5");
  const states = tiles.map(ammannStates), edges = new Map(), neighbors = tiles.map(() => []);
  states.forEach((choices, i) => {
    for (const edge of choices[0].signatures.keys()) {
      if (!edges.has(edge)) edges.set(edge, []);
      edges.get(edge).push(i);
    }
  });
  let sharedEdges = 0;
  for (const [edge, owners] of edges) {
    if (owners.length > 2) return { success: false, reason: "nonmanifold edge" };
    if (owners.length !== 2) continue;
    sharedEdges++;
    const [i, j] = owners;
    const masks = [0, 0], reverse = [0, 0];
    for (let s = 0; s < 2; s++) for (let t = 0; t < 2; t++) {
      if (ammannSignature(states[i][s], edge, directionCount) === ammannSignature(states[j][t], edge, directionCount)) {
        masks[s] |= 1 << t; reverse[t] |= 1 << s;
      }
    }
    neighbors[i].push({ at: j, masks }); neighbors[j].push({ at: i, masks: reverse });
  }
  let branches = 0;
  const solve = domains => {
    const queue = domains.map((_, i) => i);
    for (let cursor = 0; cursor < queue.length; cursor++) {
      const i = queue[cursor];
      for (const { at: j, masks } of neighbors[i]) {
        let support = 0;
        for (let s = 0; s < 2; s++) if (domains[i] & (1 << s)) support |= masks[s];
        const reduced = domains[j] & support;
        if (!reduced) return null;
        if (reduced !== domains[j]) { domains[j] = reduced; queue.push(j); }
      }
    }
    const unresolved = domains.findIndex(mask => mask === 3);
    if (unresolved < 0) return domains;
    for (const choice of [1, 2]) {
      branches++;
      const next = domains.slice(); next[unresolved] = choice;
      const answer = solve(next); if (answer) return answer;
    }
    return null;
  };
  const domains = solve(tiles.map(() => 3));
  if (!domains) return { success: false, reason: "no consistent rigid tile marking", sharedEdges, branches };
  const byTile = new Map(), orientationByTile = new Map();
  let interiorEndpoints = 0, boundaryEndpoints = 0;
  tiles.forEach((tile, i) => {
    const state = states[i][domains[i] === 1 ? 0 : 1];
    byTile.set(tile.id, state.bars); orientationByTile.set(tile.id, state.start);
    for (const bar of state.bars) for (const port of bar.ends) {
      if (edges.get(port.edge).length === 2) interiorEndpoints++; else boundaryEndpoints++;
    }
  });
  return { success: true, byTile, orientationByTile, sharedEdges, branches, interiorEndpoints, boundaryEndpoints,
    templates: 2, stripesPerTile: 5, segments: tiles.length * 5, directionCount,
    families: new Set([...byTile.values()].flat().map(bar => bar.family)).size,
    source: "Classical fixed Ammann templates; not a learned rediscovery" };
}
