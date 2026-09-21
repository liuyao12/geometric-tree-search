import assert from 'node:assert/strict';
import {createCoronaLearner,CORONA_CRITERION,markingQualifies} from '../assets/tile-corona-learning.js';
import {reduceMarking,validateMarkingReduction} from '../assets/marking-reduction.js';
import {SparseA2Marking} from '../assets/a2-tiling-engine.js';
globalThis.requestAnimationFrame=cb=>setImmediate(cb);
assert.equal(markingQualifies({valid:2,invalid:10,unresolved:0,validAccepted:2,invalidBlocked:5}),false);
assert.equal(markingQualifies({valid:2,invalid:10,unresolved:0,validAccepted:2,invalidBlocked:6}),true);
assert.equal(markingQualifies({valid:2,invalid:10,unresolved:0,validAccepted:1,invalidBlocked:10}),false);
assert.equal(markingQualifies({valid:2,invalid:10,unresolved:1,validAccepted:2,invalidBlocked:10}),false);
const expected={turtle:[304,41,263,277],hat:[320,41,279,303],mixed:[624,82,542,583]};
import {reference} from './corona-reference.mjs';
for(const [setId,[total,valid,invalid,correct]] of Object.entries(expected)){
 const learner=createCoronaLearner(setId),r=await learner.collect({budget:5000,seed:90210});
 assert.equal(r.criterion,CORONA_CRITERION);assert.equal(r.connections.length,total);assert.deepEqual(r.counts,{valid,invalid,unresolved:0});assert.equal(r.classification.correct,correct);assert.ok(r.model);learner.validateModel(r.model);assert.equal(r.classification.accepted,true);assert.equal(r.classification.validAccepted,valid);assert.equal(r.classification.invalidBlocked,correct-valid);assert.equal(r.classification.perfect,false);
 const catalog=new Set(learner.connections().map(p=>JSON.stringify([p.root,p.attachment])));for(const row of r.connections){assert.ok(catalog.delete(JSON.stringify([row.root,row.attachment])));const checked=learner.verifyCorona([row.root,row.attachment],row.placements);if(row.status==='valid')assert.ok(checked.complete);else assert.equal(row.result,'no');}
 assert.equal(catalog.size,0);
 const display=reduceMarking(r.candidateModel,{preserveInterior:true});validateMarkingReduction(display);
 const retained=new Set(display.reducedSupport.map(e=>`${e.tile}:${e.point}:${e.component}`));
 for(const root of learner.roots){
  const occupancy=learner.materialize(root).orientation.occupancy;
  for(const e of r.candidateModel.support.filter(e=>e.tile===root.tile))if(occupancy.get(e.point.join(','))?.weight===12)assert.ok(retained.has(`${e.tile}:${e.point}:${e.component}`),'Interior assignment was removed');
  assert.ok(display.reducedSupport.some(e=>e.tile===root.tile&&!occupancy.has(e.point.join(','))),'Missing exterior assignments');
 }
 for(const row of r.connections)assert.equal(learner.verifyPatch([row.root,row.attachment],display.reducedSupport).compatible,learner.verifyPatch([row.root,row.attachment],r.candidateModel.support).compatible);
 const marking=new SparseA2Marking(r.candidateModel.support);let matches=0;
 for(const row of r.connections){marking.reset([learner.materialize(row.root)]);const predicted=marking.compatible(learner.materialize(row.attachment))?'valid':'invalid';if(predicted===row.status)matches++;}assert.equal(matches,correct);
 assert.throws(()=>learner.validateModel(r.candidateModel),/qualifying one-corona/);
 const wrong={...r.candidateModel,classification:{...r.classification,correct:total,perfect:true,labels:r.connections.map(({root,attachment,status})=>({root,attachment,status}))}};assert.throws(()=>learner.validateModel(wrong),/classification counts/);
 const acceptsEverything={...r.model,support:r.model.support.map(e=>({...e,value:0}))};assert.throws(()=>learner.validateModel(acceptsEverything),/block most invalid/);
 const rejectsValid={...r.model,support:r.model.support.map((e,i)=>({...e,value:i+1}))};assert.throws(()=>learner.validateModel(rejectsValid),/rejects a valid/);
 const grown=await learner.grow({support:display.reducedSupport,target:12,budget:2000,audit:true});assert.equal(grown.result,'yes');assert.ok(learner.verifyPatch(grown.placements,r.model.support).compatible);
 const partial=learner.train(r.connections.slice(0,-1));assert.equal(partial.model,null);
 const unknown=await learner.examine({...r.connections.find(x=>x.status==='valid'),budget:0});assert.equal(unknown.status,'unresolved');assert.equal(learner.incorporate({...r,connections:r.connections.map((x,i)=>i?x:unknown)},0,unknown).model,null);
 const cases=[r.connections.find(x=>x.status==='valid'),r.connections.filter(x=>x.status==='invalid').sort((a,b)=>b.nodes-a.nodes)[0]];
 for(const row of cases){assert.equal(reference(learner,[row.root,row.attachment]),row.status==='valid');const replay=await learner.examine({...row,audit:true});assert.equal(replay.status,row.status);}
 console.log(`${setId}: all ${total} pair labels/witnesses audited; independent valid/invalid corona replay; all-valid/majority-invalid save gates and marked growth passed`);
}
