import assert from 'node:assert/strict';
import { ammannStates } from '../assets/penrose-ammann.js';
import { rationalOrientation, markingValue } from '../assets/penrose-extensions.js';
import { createPenroseGrowth } from '../assets/penrose-growth.js';
import { formatCyclotomic, inspectionPoints, inspectionText, barSamplePoints } from '../apps/penrose-model-set/point-inspection.js';

assert.equal(formatCyclotomic({ coeff: [1, 0, -1, 2], denominator: 2 }), '(1 − ζ₅² + 2ζ₅³) / 2');
assert.equal(formatCyclotomic({ coeff: [1, 1, 1, 1, 1] }), '0');
assert.equal(formatCyclotomic({ coeff: [0, -1, 0, 0] }), '−ζ₅');
const growth = createPenroseGrowth({ useMarkings: true, targetCount: 60, seed: 17 });
growth.next();
let points = inspectionPoints(growth.snapshot());
const origin = points.find(p => p.key === '0,0,0,0/1');
assert.equal(origin.t, 2); assert.equal(inspectionText(origin, true).t, 't(x) = 1/5');
assert.match(inspectionText(origin, true).m, /\(0, 0, 0, 0, 0\)/);
assert(points.some(p => p.exact.denominator > 1), 'include exact rational decoration ports');
while (!growth.next().done) {}
const snapshot = growth.snapshot(); points = inspectionPoints(snapshot, { includeIntermediate: false });
const complete = points.find(p => p.vertex && p.t === 10); assert(complete);
assert.match(inspectionText(complete, true).t, /^t\(x\) = 1 = /);
const shared = points.filter(p => !p.vertex && p.markings.size === 2); assert(shared.length > 0);
for (const p of shared) {
  const [a, b] = [...p.markings.values()];
  assert.deepEqual(a.value, b.value, 'm glues across tile boundaries');
  assert.equal(p.t, 0, 'ports are outside the stored vertex support of t');
  assert.equal(inspectionText(p, true).m, `m(x) = (${a.value.join(', ')}) · 2 tile supports compatible`, 'do not sum matching m values');
}
assert(points.filter(p => p.vertex).every(p => p.exact.denominator === 1));
console.log('ok: exact cyclotomic formatting, vertex t sums, rational marking ports, and glued (not summed) m values');

const tile = snapshot.tiles[0], state = ammannStates(tile).find(s => s.start === new Map(snapshot.orientations).get(tile.id)), bar = state.bars[0];
for (const density of [4, 8, 16]) {
  const samples = barSamplePoints(bar, 2, density);
  assert.equal(samples.length, 5 * density - 3);
  assert.equal(samples.filter(s => s.extension).length, 4 * density - 2);
  for (const sample of samples) {
    assert.equal(rationalOrientation(bar.from, bar.to, sample.point), 0);
    assert.equal(markingValue(tile, state, sample.point, 2)[bar.family], 1);
  }
}
const samples = inspectionPoints({ tiles: [tile], orientations: [[tile.id, state.start]], extent: 2 });
assert(samples.filter(p => p.intermediate && p.extension).length >= 100);
assert.match(inspectionText(samples.find(p => p.intermediate && p.extension), true).title, /Extension sample/);
console.log('ok: intermediate samples at 4/8/16 densities have exact coordinates and valid marking values');
