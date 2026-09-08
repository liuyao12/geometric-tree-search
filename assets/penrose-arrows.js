import { latticeKey } from './cyclotomic-five.js?v=20260908-speed';

// Standard Penrose P3 edge arrows: same type and direction on a shared edge.
// Andrejs Treibergs, Penrose Tiling, slide 17:
// https://www.math.utah.edu/~treiberg/PenroseSlides.pdf#page=17
// Entries follow the boundary from an acute corner: [multiplicity, direction].
// The thin template starts at the opposite acute corner to the slide, aligning
// the rigid orientation index with our Ammann template. No bars are consulted.
export const ARROW_TEMPLATES = {
  thick: [[1, 1], [2, 1], [2, -1], [1, -1]],
  thin: [[1, 1], [1, -1], [2, 1], [2, -1]]
};
const cache = new WeakMap();
export function arrowStates(tile) {
  if (cache.has(tile)) return cache.get(tile);
  const template = ARROW_TEMPLATES[tile.kind];
  if (!template || tile.exactPoints.length !== 4) throw new TypeError('Arrows require P3 rhombs');
  const keys = tile.exactPoints.map(latticeKey), acute = Math.min(...tile.weights);
  const states = tile.weights.flatMap((weight, start) => {
    if (weight !== acute) return [];
    const arrows = template.map(([type, direction], i) => {
      const k = (start + i) % 4, l = (k + 1) % 4;
      const from = direction > 0 ? k : l, to = direction > 0 ? l : k;
      return { type, from: tile.exactPoints[from], to: tile.exactPoints[to],
        edge: [keys[k], keys[l]].sort().join('|'), signature: `${type}:${keys[from]}>${keys[to]}` };
    });
    return [{ start, arrows, signatures: new Map(arrows.map(a => [a.edge, a.signature])) }];
  });
  cache.set(tile, states); return states;
}

// Independent edge-label CSP. Domains contain the two rigid orientations of
// each arrowed rhomb. Propagation plus exhaustive branching is complete for a
// finite patch. This module neither imports nor evaluates Ammann markings.
export function solveArrowDecorations(tiles) {
  const states = tiles.map(arrowStates), edges = new Map(), neighbors = tiles.map(() => []);
  states.forEach((choices, i) => {
    for (const edge of choices[0].signatures.keys()) {
      if (!edges.has(edge)) edges.set(edge, []);
      edges.get(edge).push(i);
    }
  });
  let sharedEdges = 0;
  for (const [edge, owners] of edges) {
    if (owners.length > 2) return { success: false, reason: 'nonmanifold edge' };
    if (owners.length !== 2) continue;
    sharedEdges++;
    const [i, j] = owners, masks = [0, 0], reverse = [0, 0];
    for (let s = 0; s < 2; s++) for (let t = 0; t < 2; t++) {
      if (states[i][s].signatures.get(edge) === states[j][t].signatures.get(edge)) {
        masks[s] |= 1 << t; reverse[t] |= 1 << s;
      }
    }
    neighbors[i].push({ at: j, masks }); neighbors[j].push({ at: i, masks: reverse });
  }
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
    const unresolved = domains.indexOf(3);
    if (unresolved < 0) return domains;
    for (const choice of [1, 2]) {
      const next = domains.slice(); next[unresolved] = choice;
      const answer = solve(next); if (answer) return answer;
    }
    return null;
  };
  const domains = solve(tiles.map(() => 3));
  if (!domains) return { success: false, reason: 'no consistent edge arrows', sharedEdges };
  return { success: true, sharedEdges, orientationByTile: new Map(tiles.map((tile, i) => [tile.id, states[i][domains[i] === 1 ? 0 : 1].start])) };
}
