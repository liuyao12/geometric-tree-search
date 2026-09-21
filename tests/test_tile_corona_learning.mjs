import assert from 'node:assert/strict';
import {createCoronaLearner,CORONA_CRITERION,LEGACY_CORONA_CRITERION,markingQualifies} from '../assets/tile-corona-learning.js';
import {reduceMarking,validateMarkingReduction} from '../assets/marking-reduction.js';
import {SparseA2Marking} from '../assets/a2-tiling-engine.js';
globalThis.requestAnimationFrame=cb=>setImmediate(cb);
assert.equal(markingQualifies({valid:2,invalid:10,unresolved:0,validAccepted:2,invalidBlocked:5}),false);
assert.equal(markingQualifies({valid:2,invalid:10,unresolved:0,validAccepted:2,invalidBlocked:6}),true);
assert.equal(markingQualifies({valid:2,invalid:10,unresolved:0,validAccepted:1,invalidBlocked:10}),false);
assert.equal(markingQualifies({valid:2,invalid:10,unresolved:1,validAccepted:2,invalidBlocked:10}),false);
const expected={turtle:[304,41,263,277],hat:[320,41,279,303],mixed:[624,70,554,571]};
import {reference,frontierReference} from './corona-reference.mjs';
for(const [setId,[total,valid,invalid,correct]] of Object.entries(expected)){
 const learner=createCoronaLearner(setId),trace=[];
 const r=await learner.collect({budget:5000,seed:90210,onProgress:p=>{if(p.phase==='classify')assert.equal(p.attempts,trace.filter(e=>e.type==='pair-result').length,'Count advanced before an outcome');},onSearch:e=>trace.push({type:e.type,index:e.index,status:e.status,tiles:e.placements.length})});
 const starts=trace.filter(e=>e.type==='pair-start'),outcomes=trace.filter(e=>e.type==='pair-result');
 assert.equal(starts.length,total);assert.equal(outcomes.length,total);
 for(let i=0;i<total;i++){
  assert.equal(starts[i].index,i);assert.equal(starts[i].status,undefined);assert.equal(starts[i].tiles,2);
  assert.equal(outcomes[i].index,i);assert.equal(outcomes[i].status,r.connections[i].status);
  assert.ok(trace.indexOf(starts[i])<trace.indexOf(outcomes[i]));
  if(i+1<total)assert.ok(trace.indexOf(outcomes[i])<trace.indexOf(starts[i+1]));
 }
 for(const type of ['placement','backtrack','fail','frontier-viable'])assert.ok(trace.some(e=>e.type===type));
 assert.equal(r.criterion,CORONA_CRITERION);assert.equal(r.connections.length,total);assert.deepEqual(r.counts,{valid,invalid,unresolved:0});assert.equal(r.classification.correct,correct);assert.ok(r.model);learner.validateModel(r.model);assert.equal(r.classification.accepted,true);assert.equal(r.classification.validAccepted,valid);assert.equal(r.classification.invalidBlocked,correct-valid);assert.equal(r.classification.perfect,false);
 const catalog=new Set(learner.connections().map(p=>JSON.stringify([p.root,p.attachment])));for(const row of r.connections){assert.ok(catalog.delete(JSON.stringify([row.root,row.attachment])));const checked=learner.verifyCorona([row.root,row.attachment],row.placements);if(row.status==='valid'){assert.ok(checked.complete);assert.ok(checked.frontierViable);assert.deepEqual(frontierReference(learner,row.placements).deadPoints,[]);}else assert.equal(row.result,'no');}
 assert.equal(catalog.size,0);
 const display=reduceMarking(r.candidateModel);validateMarkingReduction(display);
 const componentCounts=new Map();for(const e of display.reducedSupport){const key=`${e.tile}:${e.point}`;componentCounts.set(key,(componentCounts.get(key)??0)+1);}
 assert.ok([...componentCounts.values()].some(n=>n<3),'No individual component was freed');
 assert.ok(display.reduction.values<display.reduction.points*3);
 if(setId==='turtle')assert.equal(display.reducedSupport.filter(e=>e.point.join()==='-2,1,1').length,0,'Unnecessary center retained');
 for(const row of r.connections)assert.equal(learner.verifyPatch([row.root,row.attachment],display.reducedSupport).compatible,learner.verifyPatch([row.root,row.attachment],r.candidateModel.support).compatible);
 const marking=new SparseA2Marking(r.candidateModel.support);let matches=0;
 for(const row of r.connections){marking.reset([learner.materialize(row.root)]);const predicted=marking.compatible(learner.materialize(row.attachment))?'valid':'invalid';if(predicted===row.status)matches++;}assert.equal(matches,correct);
 assert.throws(()=>learner.validateModel(r.candidateModel),/qualifying one-corona/);
 const wrong={...r.candidateModel,classification:{...r.classification,correct:total,perfect:true,labels:r.connections.map(({root,attachment,status})=>({root,attachment,status}))}};assert.throws(()=>learner.validateModel(wrong),/classification counts/);
 const acceptsEverything={...r.model,support:r.model.support.map(e=>({...e,value:0}))};assert.throws(()=>learner.validateModel(acceptsEverything),/block most invalid/);
 const rejectsValid={...r.model,support:r.model.support.map((e,i)=>({...e,value:i+1}))};assert.throws(()=>learner.validateModel(rejectsValid),/rejects a valid/);
 const grown=await learner.grow({support:display.reducedSupport,target:12,budget:2000,audit:true});assert.equal(grown.result,'yes');assert.ok(learner.verifyPatch(grown.placements,r.model.support).compatible);
 const oldModel={...r.model,classification:{...r.model.classification,criterion:LEGACY_CORONA_CRITERION}};assert.throws(()=>learner.validateModel(oldModel),/qualifying one-corona/);learner.validateModel(oldModel,{allowLegacy:true});
 assert.throws(()=>learner.train(r.connections.map(row=>({...row,criterion:LEGACY_CORONA_CRITERION}))),/new frontier check/);
 const partial=learner.train(r.connections.slice(0,-1));assert.equal(partial.model,null);
 const unknown=await learner.examine({...r.connections.find(x=>x.status==='valid'),budget:0});assert.equal(unknown.status,'unresolved');assert.equal(learner.incorporate({...r,connections:r.connections.map((x,i)=>i?x:unknown)},0,unknown).model,null);
 const cases=[r.connections.find(x=>x.status==='valid'),r.connections.filter(x=>x.status==='invalid').sort((a,b)=>b.nodes-a.nodes)[0]];
 for(const row of cases){assert.equal(reference(learner,[row.root,row.attachment]),row.status==='valid');const replay=await learner.examine({...row,audit:true});assert.equal(replay.status,row.status);}
 console.log(`${setId}: all ${total} pair labels/witnesses audited; independent valid/invalid corona replay; all-valid/majority-invalid save gates and marked growth passed`);
}
