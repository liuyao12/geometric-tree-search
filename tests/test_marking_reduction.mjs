import assert from 'node:assert/strict';
import fs from 'node:fs';
import {SparseA2Marking,solveA2Tiling,makeHexBoundary} from '../assets/a2-tiling-engine.js';
globalThis.requestAnimationFrame=cb=>setImmediate(cb);
import {createConnectionLearner,parity} from '../assets/tile-connection-learning.js';
import {reduceMarking,validateMarkingReduction,activeMarkingSupport,CompactA2Marking} from '../assets/marking-reduction.js';
const data=JSON.parse(fs.readFileSync(new URL('../assets/data/tile-markings.json',import.meta.url)));
for(const [setId,model] of Object.entries(data.models)){
 const learner=createConnectionLearner(setId),reduced=reduceMarking(model);learner.validateModel(reduced);assert.ok(reduced.reduction.points<reduced.reduction.originalPoints);
 const bad=structuredClone(reduced);bad.reducedSupport=[];assert.throws(()=>validateMarkingReduction(bad),/lost a marking conflict/);
 const changed=structuredClone(reduced);changed.reducedSupport[0].value+=1;assert.throws(()=>learner.validateModel(changed),/Invalid reduced marking/);
 // Independent bounded translation enumeration: derive the bounding rectangle
 // from supports rather than enumerating disagreement witnesses as the reducer does.
 let conflicts=0,pairs=0;
 for(const root of learner.roots){
  const fullRoot=learner.entries(root,model.support),smallRoot=learner.entries(root,activeMarkingSupport(reduced));
  const rootValues=new Map(fullRoot.map(e=>[`${e.point}|${e.component}`,e.value])),smallValues=new Map(smallRoot.map(e=>[`${e.point}|${e.component}`,e.value]));
  const occupancy=learner.materialize(root).orientation.occupancy;
  for(const o of learner.orientations){
   if(!learner.config.allowReflections)assert.equal(parity(o.symmetry.permutation),1);
   const spec={tile:o.tile,orientation:o.index,translation:[0,0,0]},entries=learner.entries(spec,model.support),small=learner.entries(spec,activeMarkingSupport(reduced));
   const limits=[0,1].map(i=>[Math.min(...fullRoot.map(e=>e.point[i]))-Math.max(...entries.map(e=>e.point[i])),Math.max(...fullRoot.map(e=>e.point[i]))-Math.min(...entries.map(e=>e.point[i]))]);
   for(let x=limits[0][0];x<=limits[0][1];x++)for(let y=limits[1][0];y<=limits[1][1];y++){
    const delta=[x,y,-x-y];
    if([...o.occupancy.values()].some(e=>e.weight+(occupancy.get(e.point.map((v,i)=>v+delta[i]).join(','))?.weight||0)>12))continue;
    const rejects=(a,b)=>b.some(e=>{const key=`${e.point.map((v,i)=>v+delta[i])}|${e.component}`;return a.has(key)&&a.get(key)!==e.value;});
    const full=rejects(rootValues,entries),compact=rejects(smallValues,small);assert.equal(compact,full,`${setId}: ${root.tile}/${o.tile}/${o.index}/${delta}`);pairs++;if(full)conflicts++;
   }
  }
 }
 assert.equal(conflicts,reduced.reduction.pairConflicts);
 const compact=new CompactA2Marking(reduced),dense=new SparseA2Marking(model.support),seed=learner.materialize(learner.roots[0]);
 compact.reset([seed]);dense.reset([seed]);assert.equal(compact.score(seed),dense.score(seed));compact.push(seed);dense.push(seed);compact.pop(seed);dense.pop(seed);assert.equal(compact.score(seed),dense.score(seed));
 const result=await solveA2Tiling({boundary:makeHexBoundary(20),tiles:learner.config.tiles,allowReflections:learner.config.allowReflections,initialPlacements:[seed],fixedInitialPlacements:true,completePointGrowth:true,maximize:true,targetPlacements:12,nodeLimit:1500,randomSeed:10,marking:compact,auditFrontierGraph:true});
 assert.equal(result.result,'yes');assert.ok(learner.verifyPatch(result.placements.map(p=>({tile:p.tile,orientation:p.orientation.index,translation:p.translation})),model.support).compatible);
 console.log(`${setId}: ${pairs} t-legal relative placements checked; ${conflicts} marking exclusions preserved; ${reduced.reduction.originalPoints} → ${reduced.reduction.points} points`);
}
