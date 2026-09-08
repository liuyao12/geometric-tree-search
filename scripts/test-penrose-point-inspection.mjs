import assert from 'node:assert/strict';
import { createPenroseGrowth } from '../assets/penrose-growth.js';
import { formatCyclotomic, inspectionPoints, inspectionText } from '../apps/penrose-model-set/point-inspection.js';

assert.equal(formatCyclotomic({ coeff: [1, 0, -1, 2], denominator: 2 }), '(1 − ζ₅² + 2ζ₅³) / 2');
assert.equal(formatCyclotomic({ coeff: [1, 1, 1, 1, 1] }), '0');
assert.equal(formatCyclotomic({ coeff: [0, -1, 0, 0] }), '−ζ₅');
const growth = createPenroseGrowth({ useMarkings: true, targetCount: 20, seed: 17 });
growth.next();
let points = inspectionPoints(growth.snapshot());
const origin = points.find(p => p.key === '0,0,0,0/1');
assert.equal(origin.t, 2); assert.equal(inspectionText(origin, true).t, 't(x) = 1/5');
assert.match(inspectionText(origin, true).m, /undefined/);
assert(points.every(p=>p.vertex),'empty learned support has no invented marking dots');
while (!growth.next().done) {}
const snapshot = growth.snapshot(); points = inspectionPoints(snapshot);
const complete = points.find(p => p.vertex && p.t === 10); assert(complete);
assert.match(inspectionText(complete, true).t, /^t\(x\) = 1 = /);
assert(points.some(p=>p.learned&&p.exact.denominator>1),'learned exact rational points are displayed');
assert(points.some(p=>[...p.markings.values()].some(m=>m.value.includes(0))),'learned exclusion zeros are inspectable');
const shared = points.filter(p => !p.vertex && p.markings.size === 2);
for (const p of shared) {
  const [a, b] = [...p.markings.values()];
  a.value.forEach((v,j)=>{if(v!==null&&b.value[j]!==null)assert.equal(v,b.value[j], 'defined components glue');});
  assert.equal(p.t, 0, 'ports are outside the stored vertex support of t');
  assert(!inspectionText(p,true).m.includes('mismatch'));
}
assert(points.filter(p => p.vertex).every(p => p.exact.denominator === 1));
console.log('ok: exact cyclotomic formatting, vertex t sums, rational marking ports, and glued (not summed) m values');
