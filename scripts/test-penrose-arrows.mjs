import assert from 'node:assert/strict';
import { growthRhomb, interiorsOverlap } from '../assets/penrose-growth.js';
import { arrowStates, solveArrowDecorations } from '../assets/penrose-arrows.js';
import { ammannStates } from '../assets/penrose-ammann.js';

// Exhaust every edge of all ten lattice rhomb orientations, every exterior
// neighbor, and both rigid decoration states on each tile. This proves local
// equivalence for the finite prototile adjacency catalogue, not just one patch.
let pairs = 0, allowed = 0, forbidden = 0;
for (let i = 0; i < 5; i++) for (let j = i + 1; j < 5; j++) {
  const a = growthRhomb([0, 0, 0, 0, 0], i, j);
  for (let k = 0; k < 4; k++) {
    const family = a.edgeFamilies[k], low = a.exactPoints[a.edgeSigns[k] > 0 ? k : (k + 1) % 4].coeff;
    for (let other = 0; other < 5; other++) if (other !== family) for (const side of [0, 1]) {
      const b = growthRhomb(low.map((n, i) => n - (i === other ? side : 0)), Math.min(family, other), Math.max(family, other));
      if (interiorsOverlap(a, b)) continue;
      const edge = [a.vertices[k], a.vertices[(k + 1) % 4]].sort().join('|');
      for (const s of arrowStates(a)) for (const t of arrowStates(b)) {
        const arrows = s.signatures.get(edge) === t.signatures.get(edge);
        const bars = ammannStates(a).find(x => x.start === s.start).signatures.get(edge) === ammannStates(b).find(x => x.start === t.start).signatures.get(edge);
        assert.equal(arrows, bars, `edge correspondence for ${a.kind}/${b.kind}, families ${i}/${j}`);
        pairs++; arrows ? allowed++ : forbidden++;
      }
    }
  }
}
assert.equal(pairs, 640); assert(allowed > 0 && forbidden > 0);
// A geometric 3×3 parallelogram of identical rhombs is not arrow-admissible.
const periodic = [];
for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) periodic.push(growthRhomb([i, j, 0, 0, 0], 0, 1));
assert(!solveArrowDecorations(periodic).success);
assert(solveArrowDecorations([periodic[0]]).success);
console.log(`ok: ${pairs} oriented local adjacencies; ${allowed} allowed / ${forbidden} forbidden; independent arrows equal full Ammann matching; periodic patch rejected`);
