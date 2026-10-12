import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {unitLoop,gridLift,translationKey,mirror,searchInput} from '../research/knot-classifier/lattice-state.mjs';
import {regularProjection} from '../apps/knot-movie/projection.mjs';
import {colorDimension} from '../apps/knot-movie/engine.mjs';
const corpus=JSON.parse(readFileSync(new URL('../research/knot-classifier/lattice-corpus-12.json',import.meta.url)));
assert.equal(corpus.records.length,2978);assert.equal(new Set(corpus.records.map(r=>r.id)).size,2978);
for(const r of corpus.records){
  const p=unitLoop(r.vertices);assert.equal(p.length,r.unitEdges);
  if(r.grid)assert.deepEqual(gridLift(r.grid),r.vertices);
  const key=translationKey(p);
  assert.equal(translationKey([...p].reverse()),key);
  assert.equal(translationKey([...p.slice(3),...p.slice(0,3)]),key);
  assert.equal(translationKey(p.map(([x,y,z])=>[x+13,y-4,z+7])),key);
  assert.equal(translationKey(mirror(mirror(p))),key);
  assert.deepEqual(Object.keys(searchInput(r)),['vertices']);
}
assert.throws(()=>unitLoop([[0,0,0],[2,0,0],[1,0,0],[1,1,0],[0,1,0]]),/self-intersects/);
assert.throws(()=>unitLoop([[0,0,0],[1,1,0],[1,2,0],[0,2,0]]),/coordinate axis/);
assert.throws(()=>gridLift([[0,0],[1,0],[0,1],[1,1],[2,2],[3,2],[2,3],[3,3]]),/multiple/);
const trefoil=corpus.records.find(r=>r.id==='3_1');assert.notEqual(translationKey(trefoil.vertices),translationKey(mirror(trefoil.vertices)));
// An independent projector/invariant is an evaluation-only sanity check,
// never part of the lattice state module or its future search inputs.
assert.equal(colorDimension(regularProjection(unitLoop(trefoil.vertices)).word),2);
assert.equal(colorDimension(regularProjection(unitLoop(corpus.records.find(r=>r.id==='4_1').vertices)).word),1);
console.log(JSON.stringify({passed:true,latticeReferences:corpus.records.length,mirrors:true,searchMetadataStripped:true,projectionSanityChecks:2}));
