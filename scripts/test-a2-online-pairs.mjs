import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createCoronaLearner} from '../assets/tile-corona-learning.js';
import {overlapContacts,supportDomain} from './experiment-a2-online-pairs.mjs';
const dir=process.argv[2]??'/tmp/a2-online-pairs',key=r=>`${r.attachment.orientation}:${r.attachment.translation}`;
let checked=0,rescued=0;
for(const tile of ['turtle','hat'])for(const seed of [1,3]){
 const learner=createCoronaLearner(tile,{lattice:'turtle-sublattice'}),baseline=JSON.parse(fs.readFileSync(`${dir}/${tile}-baseline-pair-s${seed}.json`)),catalog=new Set(learner.connections().map(key));
 assert.equal(baseline.rows.length,catalog.size);assert.equal(new Set(baseline.rows.map(key)).size,catalog.size);assert.ok(baseline.rows.every(r=>catalog.has(key(r))));
 for(const positiveMode of ['pair','witness']){
  const r=JSON.parse(fs.readFileSync(`${dir}/${tile}-online-${positiveMode}-s${seed}.json`));
  assert.equal(r.rows[0].priorValues,0);assert.deepEqual(r.rows.map(key),baseline.rows.map(key));
  for(const [i,row]of r.rows.entries()){
   assert.equal(row.status,baseline.rows[i].status);if(row.status==='invalid')assert.equal(row.oracle?.status,'invalid');
   if(row.status==='valid')assert.ok(learner.verifyCorona([row.root,row.attachment],row.placements).complete);
   if(row.guided&&row.guided.status!=='valid'&&row.status==='valid')rescued++;
   checked++;
  }
  for(const snap of r.snapshots){
   if(snap.status!=='sat'){assert.equal(snap.support.length,0);continue;}
   const prefix=r.rows.slice(0,snap.after).filter(row=>row.status!=='unresolved');
   for(const row of prefix){const patch=row.status==='valid'&&positiveMode==='witness'?row.placements:[row.root,row.attachment];assert.equal(learner.verifyPatch(patch,snap.support).compatible,row.status==='valid');}
   const domain=supportDomain(learner,snap.halo),allowed=new Set(domain.map(e=>`${e.point}|${e.component}`));assert.ok(snap.support.every(e=>allowed.has(`${e.point}|${e.component}`)&&Number.isSafeInteger(e.value)));
   // Direct geometric overlap contacts agree with the independent patch
   // checker for each pair, including omitted components and signed action.
   const values=new Map(snap.support.map(e=>[`${e.point}|${e.component}`,e.value]));
   for(const pair of learner.connections()){
    const contacts=overlapContacts(learner,domain,[pair.root,pair.attachment]);
    const reject=contacts.some(([i,j,s])=>{const a=values.get(`${domain[i].point}|${domain[i].component}`),b=values.get(`${domain[j].point}|${domain[j].component}`);return a!==undefined&&b!==undefined&&a!==s*b;});
    assert.equal(!reject,learner.verifyPatch([pair.root,pair.attachment],snap.support).compatible);
   }
  }
 }
}
assert.ok(rescued>0,'Experiment must expose and correct provisional false rejections');
console.log(`PASS ${checked} online labels equal their independent baseline labels; every negative has unmarked authority; ${rescued} positive recoveries; all saved prefixes satisfy their observed constraints.`);
