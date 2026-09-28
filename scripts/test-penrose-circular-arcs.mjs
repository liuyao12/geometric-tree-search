import assert from 'node:assert/strict';
import {circularArcs} from '../assets/penrose-circular-arcs.js';
import {selectedPenroseProblem} from '../assets/penrose-selection-problem.js';
import {geometricPlacementAllowed} from '../assets/cyclotomic-tile-catalog.js';
import {embedding,latticeKey} from '../assets/cyclotomic-five.js';
import {num} from '../assets/penrose-polygon.js';
const problem = selectedPenroseProblem(['kite', 'dart']);
const arcs = tile => circularArcs(tile.kind, tile.exactPoints.map(p => embedding(p)));
const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
const port = (tile, edge) => {
  for (const arc of arcs(tile)) {
    if (arc.edges[0] === edge) return {point: arc.from, color: arc.color};
    if (arc.edges[1] === edge) return {point: arc.to, color: arc.color};
  }
  throw Error('Missing edge port');
};
let accepted = 0, rejected = 0;
for (const template of problem.catalog) {
  const tile = problem.resolve(template.type, num(0)), before = JSON.stringify(tile);
  const curves = arcs(tile);
  assert.equal(curves.length, 2);
  assert.deepEqual(curves.flatMap(a => a.edges).sort(), [0, 1, 2, 3]);
  assert(Math.abs(Math.abs(curves[0].sweep) - 2 * Math.PI / 5) < 1e-8);
  assert(Math.abs(Math.abs(curves[1].sweep) - (tile.kind === 'dart' ? 6 : 4) * Math.PI / 5) < 1e-8);
  const reversed = circularArcs(tile.kind, tile.exactPoints.map(p => embedding(p)).reverse());
  for (const arc of curves) {
    const other = reversed.find(a => a.family === arc.family);
    assert(distance(arc.from, other.to) < 1e-8 && distance(arc.to, other.from) < 1e-8);
  }
  assert.equal(JSON.stringify(tile), before, 'Rendering geometry must not mutate a placement');
  const seen = new Set();
  for (const vertex of tile.exactPoints) for (const other of problem.movesAt(vertex)) {
    if (seen.has(other.id)) continue;
    seen.add(other.id);
    if (!geometricPlacementAllowed(tile, other)) continue;
    let shared = 0, matches = true;
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
      if (latticeKey(tile.exactPoints[i]) !== latticeKey(other.exactPoints[(j+1)%4]) || latticeKey(tile.exactPoints[(i+1)%4]) !== latticeKey(other.exactPoints[j])) continue;
      shared++;
      const a = port(tile, i), b = port(other, j);
      matches &&= a.color === b.color && distance(a.point, b.point) < 1e-8;
    }
    if (!shared) continue;
    const allowed = problem.pairAllowed(tile, other);
    assert.equal(matches, allowed, 'Arc crossings must agree with existing P2 whole-edge rules');
    allowed ? accepted++ : rejected++;
  }
}
assert(accepted > 0 && rejected > 0);
assert.deepEqual(circularArcs('thick', []), []);
console.log(`ok: circular arcs, reversed outlines, no mutation, ${accepted} accepted and ${rejected} rejected P2 contacts across all rigid orientations`);
