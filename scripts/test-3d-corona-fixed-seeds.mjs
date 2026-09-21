import assert from 'node:assert/strict';
import {CoronaGraph,checkCorona,verifyCorona,placementKey,pointKey,add,allowedTranslation} from '../apps/3d-lattice-tiler/corona-graph.js';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {neighboringPairs,pointSymmetries} from '../apps/3d-lattice-tiler/marking-learning.js';
import {prepareVoxelPointModel} from '../apps/3d-lattice-tiler/voxel-point-model.js';
import {POLYCUBE_GCTS_CANDIDATES} from '../assets/polycube-census-candidates.js';
const collect=async stream=>{let last;for await(const e of stream)last=e;return last;};
function audit(g){
 g.audit();
 for(const k of g.active){
  const pos=k.split(',').map(Number),expected=new Set();
  for(let oi=0;oi<g.model.orientations.length;oi++)for(const anchor of g.model.orientations[oi].cells){
   const translation=pos.map((v,i)=>v-anchor.pos[i]),id=placementKey({oi,translation});
   if(!allowedTranslation(g.model,translation)||g.used.has(id))continue;
   if(g.model.orientations[oi].cells.every(c=>(g.totals.get(pointKey(add(c.pos,translation)))??0)+c.weight<=g.model.capacity))expected.add(id);
  }
  assert.deepEqual(new Set([...g.point(k).incident].filter(c=>c.valid).map(c=>c.id)),expected);
 }
}
const state=g=>JSON.stringify({totals:[...g.totals].sort(),active:[...g.active].sort(),generations:[...g.generations].map(([k,v])=>[k,[...v]]).sort(),placements:g.descriptors()});
for(const tile of ['cube','a2_hexagonal_prism','a2_turtle_prism']){
 const model=prepareModel({tile,radius:1,mirrors:true}),pairs=[...neighboringPairs(model,pointSymmetries(model))];
 for(const pair of pairs.filter((_,i)=>i%Math.max(1,Math.floor(pairs.length/8))===0)){
  const plain=new CoronaGraph(model,{retainBranchCaches:true}),fixed=new CoronaGraph(model,{fixed:pair,retainBranchCaches:false});
  const roots=[];for(const p of pair){plain.apply(p,{root:true});roots.push(fixed.apply(p,{root:true}));}
  audit(plain);audit(fixed);assert.deepEqual(fixed.descriptors(),plain.descriptors());
  const baseline=state(fixed),cacheCounts=[fixed.points.size,fixed.candidates.size,fixed.dependencyEntries,fixed.sites.size],choice=fixed.schedule();
  if(choice.point){for(const c of [...choice.point.incident].filter(c=>c.valid).slice(0,3)){
   const undo=fixed.apply(c);audit(fixed);const next=fixed.schedule();
   if(next.point){const child=[...next.point.incident].find(c=>c.valid);if(child){const second=fixed.apply(child);audit(fixed);fixed.rollback(second);audit(fixed);}}
   fixed.rollback(undo);audit(fixed);assert.equal(state(fixed),baseline);assert.deepEqual([fixed.points.size,fixed.candidates.size,fixed.dependencyEntries,fixed.sites.size],cacheCounts);
  }}
  assert.throws(()=>fixed.rollback(roots.at(-1)),/fixed oracle seed/);assert.equal(state(fixed),baseline);
  assert.ok(fixed.dependencyEntries<=plain.dependencyEntries||fixed.points.size>plain.points.size);
  const results=[];for(const old of [true,false])results.push(await collect(checkCorona(model,pair,{nodes:500,fixedSeedFilter:!old,retainBranchCaches:old,audit:true})));
  assert.deepEqual(results.map(r=>[r.status,r.reason,r.nodes,r.backtracks,r.placements])[0],results.map(r=>[r.status,r.reason,r.nodes,r.backtracks,r.placements])[1]);
  if(results[1].status==='valid')assert.ok(verifyCorona(model,pair,results[1].placements).complete);
 }
 console.log(`PASS ${tile}: fixed-seed filtering preserves complete domains, rollback and search trace.`);
}
const cube=prepareModel({tile:'a2_hexagonal_prism',radius:1}),p=[...neighboringPairs(cube,pointSymmetries(cube))][0];
const plain=await collect(checkCorona(cube,p,{fixedSeedFilter:false})),filtered=await collect(checkCorona(cube,p));
assert.ok(filtered.fixedRejected>0);assert.ok(filtered.dependencyEntries<plain.dependencyEntries);
console.log('PASS permanent seed exclusions actually reduce dependency storage; no reversible prefix is cached as permanent.');
assert.throws(()=>new CoronaGraph(cube,{retainBranchCaches:true,filterAtBirth:true}),/cache rollback/);
// Exercise genuinely 3D overlapping candidate dependencies in the geometric
// model, including a sibling after discarding the first child's caches.
const hard=prepareVoxelPointModel(POLYCUBE_GCTS_CANDIDATES[0].voxels),seeds=neighboringPairs(hard,pointSymmetries(hard)).next().value,graph=new CoronaGraph(hard,{fixed:seeds,retainBranchCaches:false});
for(const p of seeds)graph.apply(p,{root:true});audit(graph);const parent=state(graph),choices=[...graph.schedule().point.incident].filter(c=>c.valid).slice(0,2);
for(const c of choices){const undos=[graph.apply(c)];audit(graph);for(let depth=0;depth<4;depth++){const s=graph.schedule();if(!s.point||s.kind==='dead')break;const child=[...s.point.incident].find(c=>c.valid);if(!child)break;undos.push(graph.apply(child));audit(graph);}while(undos.length){graph.rollback(undos.pop());audit(graph);}assert.equal(state(graph),parent);}
const traces=[];for(const retainBranchCaches of [true,false])traces.push(await collect(checkCorona(hard,seeds,{retainBranchCaches,nodes:100})));
assert.deepEqual(traces.map(r=>[r.status,r.reason,r.nodes,r.backtracks,r.placements])[0],traces.map(r=>[r.status,r.reason,r.nodes,r.backtracks,r.placements])[1]);
console.log('PASS hard 3D voxel model: independent domains, nested/sibling rollback and identical resolved trace.');
