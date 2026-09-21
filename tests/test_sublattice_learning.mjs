import assert from 'node:assert/strict';
import {createCoronaLearner,parity} from '../assets/tile-corona-learning.js';
import {onTurtleSublattice as onLattice} from '../assets/learning-lattice.js';
import {reduceMarking,activeMarkingSupport} from '../assets/marking-reduction.js';
import {markingValues} from '../assets/marking-library.js';
import {markingMetadata} from '../assets/marking-metadata.js';
import {a2Transform} from '../assets/a2-tiling-engine.js';
import {reference,frontierReference} from './corona-reference.mjs';
globalThis.requestAnimationFrame=cb=>setImmediate(cb);
const lattice='turtle-sublattice';
for(const [setId,[total,valid,invalid,blocked]] of Object.entries({turtle:[247,41,206,176],hat:[227,41,186,166],mixed:[473,71,402,344]})){
 const learner=createCoronaLearner(setId,{lattice}),full=createCoronaLearner(setId);
 assert.notEqual(learner,full);assert.equal(createCoronaLearner(setId,{lattice}),learner);
 assert.throws(()=>createCoronaLearner(setId,{lattice:'unknown'}),/Unknown learning lattice/);
 for(const o of learner.orientations){
  const original=full.orientations.find(p=>p.index===o.index&&p.tile===o.tile);
  assert.deepEqual([...o.occupancy],[...original.occupancy].filter(([,e])=>onLattice(e.point)));
  if(setId==='mixed')assert.equal(parity(o.symmetry.permutation),1);
 }
 assert.throws(()=>learner.materialize({...learner.roots[0],translation:[1,-1,0]}),/Invalid placement/);
 const r=await learner.collect();
 assert.equal(r.lattice,lattice);assert.equal(r.settings.lattice,lattice);
 assert.equal(r.connections.length,total);assert.deepEqual(r.counts,{valid,invalid,unresolved:0});
 assert.equal(r.classification.validAccepted,valid);assert.equal(r.classification.invalidBlocked,blocked);
 assert.equal(r.classification.accepted,true);assert.ok(r.model);
 const candidate=r.candidateModel;assert.ok(candidate.support.every(e=>onLattice(e.point)));
 learner.validateCandidate(candidate);assert.throws(()=>full.validateCandidate(candidate),/different lattice/);
 assert.equal(markingValues(candidate),markingValues({...candidate,lattice:'A2'}),'Training provenance does not change marking values');
 const reduced=reduceMarking(candidate,{preserveInterior:true});learner.validateCandidate(reduced);
 assert.equal(markingMetadata(reduced).lattice,lattice);
 for(const row of r.connections){
  const pair=[row.root,row.attachment];assert.ok(pair.every(p=>onLattice(p.translation)));
  assert.ok(learner.corePoints(pair).every(onLattice));
  if(row.status==='valid'){assert.ok(learner.verifyCorona(pair,row.placements).complete);assert.deepEqual(frontierReference(learner,row.placements).deadPoints,[]);}
  assert.equal(learner.verifyPatch(pair,candidate.support).compatible,learner.verifyPatch(pair,activeMarkingSupport(reduced)).compatible);
 }
 // Independent bounded translation enumeration includes mark-only contacts,
 // not just the labeled neighboring pairs, and uses restricted t-capacities.
 let conflicts=0;
 for(const root of learner.roots)for(const o of learner.orientations){
  const spec={tile:o.tile,orientation:o.index,translation:[0,0,0]},left=learner.entries(root,candidate.support),right=learner.entries(spec,candidate.support);
  const smallLeft=learner.entries(root,activeMarkingSupport(reduced)),smallRight=learner.entries(spec,activeMarkingSupport(reduced));
  const fullValues=new Map(left.map(e=>[`${e.point}|${e.component}`,e.value])),smallValues=new Map(smallLeft.map(e=>[`${e.point}|${e.component}`,e.value]));
  const occupancy=learner.materialize(root).orientation.occupancy;
  const bounds=[0,1].map(i=>[Math.min(...left.map(e=>e.point[i]))-Math.max(...right.map(e=>e.point[i])),Math.max(...left.map(e=>e.point[i]))-Math.min(...right.map(e=>e.point[i]))]);
  for(let x=bounds[0][0];x<=bounds[0][1];x++)for(let y=bounds[1][0];y<=bounds[1][1];y++){
   const delta=[x,y,-x-y];if(!onLattice(delta))continue;
   if([...o.occupancy.values()].some(e=>e.weight+(occupancy.get(e.point.map((v,i)=>v+delta[i]).join())?.weight||0)>12))continue;
   const rejects=(a,b)=>b.some(e=>{const key=`${e.point.map((v,i)=>v+delta[i])}|${e.component}`;return a.has(key)&&a.get(key)!==e.value;});
   const fullRejects=rejects(fullValues,right);assert.equal(rejects(smallValues,smallRight),fullRejects);if(fullRejects)conflicts++;
  }
 }
 assert.equal(conflicts,reduced.reduction.pairConflicts);
 const samples=[r.connections.find(x=>x.status==='valid'),r.connections.filter(x=>x.status==='invalid').sort((a,b)=>b.nodes-a.nodes)[0]];
 for(const row of samples){assert.equal(reference(learner,[row.root,row.attachment]),row.status==='valid');assert.equal((await learner.examine({...row,audit:true})).status,row.status);}
 for(const o of learner.orientations)for(const e of candidate.support)assert.ok(onLattice(a2Transform(e.point,o.symmetry)));
 if(r.model){
  learner.validateModel({...reduced,classification:r.model.classification});
  const grown=await learner.grow({support:activeMarkingSupport(reduced),target:24,budget:3000,audit:true});
  assert.equal(grown.result,'yes');assert.ok(grown.placements.every(p=>onLattice(p.translation)));assert.ok(learner.verifyPatch(grown.placements,candidate.support).compatible);
  // A saved marking belongs to the tile system. Its training-domain validation
  // is separate from application to the full tiling lattice.
  const fullGrown=await full.grow({support:activeMarkingSupport(reduced),target:24,budget:3000,audit:true});
  assert.equal(fullGrown.result,'yes');assert.ok(full.verifyPatch(fullGrown.placements,activeMarkingSupport(reduced)).compatible);
  assert.ok(full.verifyPatch(fullGrown.placements,candidate.support).compatible);
  assert.ok(full.materialize(full.roots[0]).orientation.occupancy.size>learner.materialize(learner.roots[0]).orientation.occupancy.size);

 }else assert.throws(()=>learner.validateModel(candidate),/qualifying one-corona/);
 console.log(`${setId} sublattice: ${valid} valid, ${invalid} invalid, ${blocked} blocked; independent corona replay, domain isolation and exhaustive reduction passed`);
}
// Existing locally trained models without a lattice field retain A2 semantics.
const base=createCoronaLearner('turtle'),legacy=base.encode([{placements:base.roots}]);delete legacy.lattice;base.validateCandidate(legacy);
assert.throws(()=>createCoronaLearner('turtle',{lattice}).validateCandidate(legacy),/different lattice/);
