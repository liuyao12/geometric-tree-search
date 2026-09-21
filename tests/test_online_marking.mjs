import assert from 'node:assert/strict';
import {createCoronaLearner} from '../assets/tile-corona-learning.js';
globalThis.requestAnimationFrame=cb=>setImmediate(cb);
// Fresh labels, prefix-only learning, and independent geometric replay. No
// browser-learned assignments or precomputed labels are bundled with the test.
for(const lattice of ['A2','turtle-sublattice'])for(const set of ['turtle','hat','mixed']){
 const learner=createCoronaLearner(set,{lattice}),prefix=[],updates=[];let maxMs=0,totalMs=0;
 const report=await learner.collect({onLearning:async update=>{
  assert.equal(update.attempts,updates.length+1);
  assert.equal(update.counts.valid+update.counts.invalid+update.counts.unresolved,update.attempts);
  prefix.push({root:update.root,attachment:update.attachment,status:update.status,criterion:'viable-pair-one-corona-v2'});
  let blocked=0;
  if(update.model){
   assert.equal(update.model.marking,undefined);assert.equal(update.model.classification,undefined,'A provisional model must not be saveable');
   assert.throws(()=>learner.validateModel(update.model),/qualifying one-corona/);
   for(const row of prefix){const agrees=learner.verifyPatch([row.root,row.attachment],update.model.support).compatible;if(row.status==='valid')assert.ok(agrees,'An earlier positive became incompatible');if(row.status==='invalid'&&!agrees)blocked++;}
  }
  assert.equal(update.invalidBlocked,blocked);
  if([1,10,50,150].includes(update.attempts)){
   const batch=learner.train(prefix);assert.deepEqual(update.model,batch.candidateModel);assert.equal(update.validAccepted,batch.classification.validAccepted);assert.equal(blocked,batch.classification.invalidBlocked);
  }
  maxMs=Math.max(maxMs,update.elapsedMs);totalMs+=update.elapsedMs;updates.push(update);
 }});
 assert.equal(updates.length,report.connections.length);
 assert.deepEqual(updates.at(-1).model,report.candidateModel);
 assert.equal(updates.at(-1).invalidBlocked,report.classification.invalidBlocked);
 assert.ok(updates.some((u,i)=>i&&u.model&&JSON.stringify(u.model.support)!==JSON.stringify(updates[i-1].model?.support)),'No evolving values');
 // Add an unknown label: it must not become an equality or an exclusion label.
 const stream=learner.createOnlineTrainer(),positive=report.connections.find(r=>r.status==='valid'),negative=report.connections.find(r=>r.status==='invalid');
 const before=stream.add(positive),after=stream.add({...negative,status:'unresolved'});
 assert.deepEqual(after.model,before.model);assert.equal(after.counts.unresolved,1);assert.equal(after.invalidBlocked,0);
 console.log(`${set}/${lattice}: ${updates.length} ordered updates, every prefix replayed; final batch match; solver ${totalMs.toFixed(0)} ms total / ${maxMs.toFixed(1)} ms max`);
}
