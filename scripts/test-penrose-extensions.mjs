import assert from 'node:assert/strict';
import { createPenroseGrowth } from '../assets/penrose-growth.js';
import { makeCyclotomicSearch } from '../assets/penrose-model-set.js';
import { ammannStates, solveAmmannDecorations } from '../assets/penrose-ammann.js';
import { extendBar, extensionStatesCompatible, markingValue, rationalOrientation } from '../assets/penrose-extensions.js';
import { latticeKey } from '../assets/cyclotomic-five.js';

for (const extent of [-1, .1, 4.25, NaN]) assert.throws(() => createPenroseGrowth({ extent }));
for (const phaseCode of [0, 47, 170]) {
  const reference = makeCyclotomicSearch({ targetCount: 80, phaseCode }); assert(reference.success);
  for (const extent of [.25, 2, 4]) {
    const result = solveAmmannDecorations(reference.solution, { extent });
    assert(result.success, `known Penrose patch must survive extent ${extent}, phase ${phaseCode}`);
  }
}
const run = extent => {
  const g = createPenroseGrowth({ useMarkings: true, targetCount: 40, nodeLimit: 10000, seed: 17, extent });
  while (!g.next().done) {} return g.snapshot();
};
const zero = run(0), extended = run(2);
assert.equal(zero.status, 'target reached'); assert.equal(extended.status, 'target reached');
assert(extended.stats.proposals < zero.stats.proposals);
assert.equal(extended.stats.edgeChecks, 0);
const assignment = new Map(zero.orientations);
let nonneighborConflict = false;
for (let i = 0; i < zero.tiles.length; i++) for (let j = i + 1; j < zero.tiles.length; j++) {
  const a = zero.tiles[i], b = zero.tiles[j];
  const sa = ammannStates(a).find(s => s.start === assignment.get(a.id)), sb = ammannStates(b).find(s => s.start === assignment.get(b.id));
  const shared = [...sa.signatures.keys()].some(k => sb.signatures.has(k));
  if (!shared && !extensionStatesCompatible(a, sa, b, sb, 2)) nonneighborConflict = true;
}
assert(nonneighborConflict, 'positive extent must detect incompatible tiles without a shared edge');
const tile = extended.tiles[0], state = ammannStates(tile).find(s => s.start === new Map(extended.orientations).get(tile.id));
const bar = state.bars[0], ex = extendBar(bar, 2);
assert.notEqual(latticeKey(ex.from), latticeKey(bar.from));
assert.equal(latticeKey(extendBar(bar, 0).from), latticeKey(bar.from));
assert.equal(rationalOrientation(bar.from, bar.to, ex.from), 0);
assert.equal(markingValue(tile, state, ex.from, 2)[bar.family], 1);
assert.equal(markingValue(tile, state, ex.from, 0), null);
assert.deepEqual(markingValue(tile, state, tile.exactPoints[0], 2), [0, 0, 0, 0, 0]);
console.log(JSON.stringify({ok:true,referenceTiles:240,extents:[.25,2,4],nonneighborConflict,proposals:[zero.stats.proposals,extended.stats.proposals],backtracks:[zero.stats.backtracks,extended.stats.backtracks]}));
