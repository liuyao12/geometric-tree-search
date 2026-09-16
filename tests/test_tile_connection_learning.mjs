import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createConnectionLearner,TILE_SETS,parity} from '../assets/tile-connection-learning.js';
import {a2Add,A2_SYMMETRIES,a2Transform,tileOrientations,A2_TILE_LOOPS} from '../assets/a2-tiling-engine.js';
globalThis.requestAnimationFrame=cb=>setTimeout(cb,0);
const id=p=>`${p.tile}:${p.orientation}:${p.translation}`;
function totals(learner,specs){const sums=new Map();for(const spec of specs){const p=learner.materialize(spec);for(const e of p.orientation.occupancy.values()){const key=a2Add(e.point,p.translation).join();sums.set(key,(sums.get(key)||0)+e.weight);}}return sums;}
function legalAt(learner,specs,point){const sums=totals(learner,specs),used=new Set(specs.map(id)),legal=new Map();
 for(const o of learner.orientations)for(const e of o.occupancy.values()){
  const translation=point.map((v,i)=>v-e.point[i]),spec={tile:o.tile,orientation:o.index,translation},token=id(spec);if(used.has(token)||legal.has(token))continue;
  if([...o.occupancy.values()].every(v=>(sums.get(a2Add(v.point,translation).join())||0)+v.weight<=12))legal.set(token,spec);
 }return legal;
}
const expected={turtle:[304,39,263,2,236],hat:[320,40,279,1,262],mixed:[624,69,554,1,501]};
for(const setId of Object.keys(TILE_SETS)){
 const learner=createConnectionLearner(setId),report=JSON.parse(fs.readFileSync(new URL(`../assets/data/tile-connections-${setId}.json`,import.meta.url)));
 const [count,extended,dead,unresolved,separated]=expected[setId];assert.equal(report.attachmentCount,count);assert.deepEqual(report.counts,{extended,dead,unresolved});assert.equal(report.encoding.deadSeparated,separated);assert.equal(report.encoding.extendedRejected,0);
 assert.equal(learner.validateModel(report.model),report.model);assert.deepEqual(learner.encode(report.samples),report.model);assert.ok(report.model.nonzero>0);
 // Enumerate integer translations independently of the support-alignment collector.
 const independent=new Set();
 for(const root of learner.roots){const support=learner.materialize(root).orientation.occupancy,pts=[...support.values()],xs=pts.map(e=>e.point[0]),ys=pts.map(e=>e.point[1]);
  for(const o of learner.orientations){const pts2=[...o.occupancy.values()],ox=pts2.map(e=>e.point[0]),oy=pts2.map(e=>e.point[1]);
   for(let x=Math.min(...xs)-Math.max(...ox);x<=Math.max(...xs)-Math.min(...ox);x++)for(let y=Math.min(...ys)-Math.max(...oy);y<=Math.max(...ys)-Math.min(...oy);y++){
    const spec={tile:o.tile,orientation:o.index,translation:[x,y,-x-y]};if(id(spec)===id(root))continue;let touches=false,valid=true;
    for(const e of pts2){const prior=support.get(a2Add(e.point,spec.translation).join());if(prior){touches=true;if(prior.weight+e.weight>12)valid=false;}}
    if(touches&&valid)independent.add(`${id(root)}>${id(spec)}`);
   }
  }
 }
 assert.equal(independent.size,count);assert.deepEqual(new Set(learner.connections().map(p=>`${id(p.root)}>${id(p.attachment)}`)),independent);
 assert.deepEqual(new Set(report.connections.map(p=>`${id(p.root)}>${id(p.attachment)}`)),independent);
 for(const row of report.connections){
  learner.verifyPatch(row.placements);
  assert.ok([row.root,row.attachment].every(p=>row.placements.some(q=>id(p)===id(q))));
  if(row.status==='extended'){
   assert.ok(learner.verifyPatch(row.placements,report.model.support).compatible);
   for(const [point,n] of totals(learner,row.placements))if(n<12)assert.ok(legalAt(learner,row.placements,point.split(',').map(Number)).size>0);
  }else if(row.status==='dead'){
   assert.equal(legalAt(learner,row.lastFailure.placements,row.lastFailure.point.split(',').map(Number)).size,0);
   const replay=await learner.examine({...row,audit:true});assert.equal(replay.status,'dead');assert.equal(replay.nodes,row.nodes);
  }
 }
 const signatures=report.samples.map(s=>learner.canonicalPatch(s.placements));assert.equal(new Set(signatures).size,signatures.length);assert.deepEqual(signatures,report.samples.map(s=>s.canonical));
 for(const sym of A2_SYMMETRIES.filter(s=>learner.config.allowReflections||parity(s.permutation)>0)){
  const specs=report.samples[0].placements.map(spec=>{const old=learner.materialize(spec).orientation.symmetry,sign=sym.sign*old.sign,perm=sym.permutation.map(j=>old.permutation[j]),orientation=learner.orientations.find(o=>o.tile===spec.tile&&o.symmetry.sign===sign&&o.symmetry.permutation.every((v,i)=>v===perm[i])).index;return {tile:spec.tile,orientation,translation:a2Add(a2Transform(spec.translation,sym),[4,-3,-1])};});
  assert.equal(learner.canonicalPatch(specs),report.samples[0].canonical);assert.ok(learner.verifyPatch(specs,report.model.support).compatible);
 }
 assert.equal(report.markedCheck.result,'yes');assert.equal(report.markedCheck.placements.length,24);assert.ok(learner.verifyPatch(report.markedCheck.placements,report.model.support).compatible);
 const audited=await learner.grow({support:report.model.support,target:12,budget:1500,seed:701,audit:true});assert.equal(audited.result,'yes');
 const row=report.connections.find(r=>r.status==='extended'),i=report.connections.indexOf(row),timeout=await learner.examine({...row,budget:0,target:24});assert.equal(timeout.status,'unresolved');assert.equal(learner.incorporate(report,i,timeout).connections[i].status,'extended');
 if(setId==='mixed'){
  assert.equal(learner.orientations.length,12);assert.ok(learner.orientations.every(o=>parity(o.symmetry.permutation)>0));assert.equal(new Set(report.markedCheck.placements.map(p=>p.tile)).size,2);
  const reflection=tileOrientations('hat',A2_TILE_LOOPS.hat).find(o=>parity(o.symmetry.permutation)<0);assert.throws(()=>learner.materialize({tile:'hat',orientation:reflection.index,translation:[0,0,0]}));
 }
 console.log(JSON.stringify({setId,passed:true,connections:count,deadReplays:dead,extendedFrontiers:extended,encodedFailures:separated,markedGrowth:24}));
}
const turtle=createConnectionLearner('turtle'),hat=JSON.parse(fs.readFileSync(new URL('../assets/data/tile-connections-hat.json',import.meta.url)));assert.throws(()=>turtle.validateModel(hat.model));
