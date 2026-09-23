import assert from 'node:assert/strict';
import {createGrowthState,createGrowthStateFromPatch,enumerateGrowthCandidates,growOne,shrinkOne} from '../3d-reptiles/chair/chair-gcts.js';
import {createReliefPointModel} from '../3d-reptiles/chair/relief-points.js';
import {chairLeaves,ROTATIONS,verifyPatch} from '../3d-reptiles/chair/chair44.js';
const summary=[];
for(const [rule,neighbors] of [['arrows',44],['relief-offset',128],['relief-centered',316]]) {
 let state=createGrowthState(2,rule);
 assert.equal(enumerateGrowthCandidates(state).candidateNodes.size,neighbors);
 const root=structuredClone(state.placements);
 const model=rule==='arrows'?null:createReliefPointModel({centered:rule==='relief-centered'});
 for(let i=0;i<100&&!state.complete;i++) {
  const previous=state,snapshot=JSON.stringify({...previous,history:undefined});
  state=growOne(state);
  assert.equal(JSON.stringify({...previous,history:undefined}),snapshot,'Step and rollback never mutate the prior snapshot');
  assert.strictEqual(shrinkOne(state),previous,'Undo includes rule, counters, generations, and branch stack');
  assert.deepEqual(state.placements.slice(0,1),root);
  if(model)model.indexState(state.placements);
  assert.equal(enumerateGrowthCandidates(state).dead,false,'Finite pause has a viable global frontier');
 }
 assert.equal(state.status,'consistent finite patch');assert.equal(state.placements.length,64);
 const continued=growOne(state);assert.equal(continued.placements.length,65);
 assert.strictEqual(shrinkOne(continued),state);
 summary.push({rule,neighbors,tiles:64,branches:state.branchDecisions,backtracks:state.solverBacktracks,forced:state.forcedPlacements});
 if(!model)continue;
 for(const level of [0,1,2]) {
  const seed=createGrowthStateFromPatch(chairLeaves(level,[-3,7,2],ROTATIONS[7]),rule);
  const next=growOne(seed);
  assert.equal(next.placements.length,seed.placements.length+1);
  assert.deepEqual(next.placements.slice(0,seed.placements.length),seed.placements);
  assert.strictEqual(shrinkOne(next),seed);
 }
}
assert.ok(summary[2].branches>summary[1].branches);
assert.ok(summary[2].backtracks>summary[1].backtracks);
// This centered-only contact passes geometric packing and the initial frontier,
// but forces a third tile and then fails. No arrow filter may pre-reject it.
const pair=[{variantId:0,origin:[0,0,0]},{variantId:7,origin:[2,-1,1]}];
assert.equal(verifyPatch(pair).valid,false);
const seed=createGrowthStateFromPatch(pair,'relief-centered');
const before=JSON.stringify(seed),graph=enumerateGrowthCandidates(seed);
assert.equal(graph.dead,false);assert.equal(graph.forced,true);
const failed=growOne(seed);
assert.equal(failed.status,'exhausted');assert.equal(failed.forcedPlacements,1);
assert.equal(JSON.stringify(seed),before);
assert.strictEqual(shrinkOne(failed),seed);
assert.throws(()=>createGrowthStateFromPatch(pair,'arrows'),/Invalid/);
assert.throws(()=>createGrowthState(2,'unknown'),/Unknown/);
console.log(JSON.stringify(summary));
