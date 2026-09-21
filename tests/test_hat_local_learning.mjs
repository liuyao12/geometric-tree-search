import assert from 'node:assert/strict';
import {collect,HAT,ORIENTATIONS,attachments,encode,verifyPatch,canonicalPatch,grow,materialize,examine,summarize,incorporate,ROOT,conflictWitness} from '../assets/hat-local-learning.js';
import {A2_SYMMETRIES,a2Transform,a2Add,solveA2Tiling,makeHexBoundary,NoA2Marking} from '../assets/a2-tiling-engine.js';
globalThis.requestAnimationFrame=callback=>setImmediate(callback);
const report=await collect();
const signatures=new Set();for(const sample of report.samples){assert.equal(verifyPatch(sample.placements).tiles,12);assert.ok(sample.placements.some(p=>p.orientation===sample.attachment.orientation&&p.translation.join()===sample.attachment.translation.join()));assert.ok(sample.placements.some(p=>p.orientation===0&&p.translation.join()==='0,0,0'));const signature=canonicalPatch(sample.placements);assert.ok(!signatures.has(signature));signatures.add(signature);assert.equal(signature,sample.canonical);}
const inferred=encode(report.samples);assert.deepEqual(inferred,report.model);
assert.equal(report.connections.length,320);assert.deepEqual(report.counts,{extended:40,dead:279,unresolved:1});
assert.deepEqual(report.encoding,{deadSeparated:262,deadUnseparated:17,extendedRejected:0,unresolvedRejected:0});
assert.equal(report.samples.length,36);assert.equal(inferred.sampleCount,36);
assert.deepEqual(summarize(report.connections,report.config,report.elapsedMs),report);
assert.ok(!('training' in report));assert.ok(!('test' in report));
const independent=new Set();
const root=[...HAT.occupancy.values()],xs=root.map(e=>e.point[0]),ys=root.map(e=>e.point[1]);
for(const o of ORIENTATIONS){const points=[...o.occupancy.values()],ox=points.map(e=>e.point[0]),oy=points.map(e=>e.point[1]);for(let x=Math.min(...xs)-Math.max(...ox);x<=Math.max(...xs)-Math.min(...ox);x++)for(let y=Math.min(...ys)-Math.max(...oy);y<=Math.max(...ys)-Math.min(...oy);y++){
 if(o.index===0&&x===0&&y===0)continue;const translation=[x,y,-x-y];let contact=false,valid=true;
 for(const e of points){const at=a2Add(e.point,translation).join(','),prior=HAT.occupancy.get(at);if(prior){contact=true;if(prior.weight+e.weight>12)valid=false;}}
 if(contact&&valid)independent.add(`${o.index}:${translation}`);
}}
assert.deepEqual(new Set(attachments().map(p=>`${p.orientation}:${p.translation}`)),independent);assert.equal(independent.size,320);
const survivors=attachments().filter(p=>verifyPatch([{orientation:0,translation:[0,0,0]},p],inferred.support).compatible).length;assert.equal(survivors,58);
for(const sym of A2_SYMMETRIES){const transformed=report.samples[0].placements.map(spec=>{const p=materialize(spec),old=p.orientation.symmetry;const sign=sym.sign*old.sign,permutation=sym.permutation.map(j=>old.permutation[j]);const orientation=ORIENTATIONS.find(o=>o.symmetry.sign===sign&&o.symmetry.permutation.every((v,i)=>v===permutation[i])).index;return{orientation,translation:a2Add(a2Transform(spec.translation,sym),[4,-3,-1])};});assert.equal(canonicalPatch(transformed),report.samples[0].canonical);assert.equal(verifyPatch(transformed,inferred.support).compatible,true);}
assert.throws(()=>verifyPatch([...report.samples[0].placements,report.samples[0].placements[0]]));
// This t-legal pair has a global dead frontier. It must not be silently
// replaced by another attachment, as the original provisional-prefix API permits.
const fixed=await grow({initial:[{orientation:0,translation:[0,0,0]},{orientation:7,translation:[6,0,-6]}],seed:3974,target:12,budget:120});assert.equal(fixed.result,'no');assert.equal(fixed.placements.length,2);assert.equal(fixed.nodes,0);
const provisional=await solveA2Tiling({boundary:makeHexBoundary(10),tiles:['hat'],maximize:true,targetPlacements:12,nodeLimit:120,randomSeed:3974,marking:new NoA2Marking(),initialPlacements:[materialize({orientation:0,translation:[0,0,0]}),materialize({orientation:7,translation:[6,0,-6]})]});assert.equal(provisional.result,'yes');assert.ok(!provisional.placements.some(p=>p.orientation.index===7&&p.translation.join()==='6,0,-6'));
const audited=await grow({seed:7,support:inferred.support,target:12,budget:150,audit:true});assert.equal(audited.result,'yes');assert.equal(audited.verification.compatible,true);
// Re-enumerate legal candidates independently from point capacities, with no
// new-point requirement, learned marking, engine graph, or spatial boundary.
function legalAt(specs,point){
 const sums=new Map(),used=new Set(specs.map(s=>`${s.orientation}:${s.translation}`));
 for(const spec of specs){const p=materialize(spec);for(const e of p.orientation.occupancy.values()){const key=a2Add(e.point,p.translation).join();sums.set(key,(sums.get(key)||0)+e.weight);}}
 const candidates=new Map();
 for(const o of ORIENTATIONS)for(const e of o.occupancy.values()){
  const translation=point.map((v,i)=>v-e.point[i]),id=`${o.index}:${translation}`;
  if(used.has(id)||candidates.has(id))continue;
  if([...o.occupancy.values()].every(v=>(sums.get(a2Add(v.point,translation).join())||0)+v.weight<=12))candidates.set(id,{orientation:o.index,translation});
 }
 return candidates;
}
for(const row of report.connections){
 assert.equal(verifyPatch(row.placements).conflicts,0);
 assert.deepEqual(row.codeWitness,conflictWitness([ROOT,row.attachment],inferred.support));
 if(row.status==='dead'){
  assert.ok(row.lastFailure);
  assert.equal(legalAt(row.lastFailure.placements,row.lastFailure.point.split(',').map(Number)).size,0);
  const replay=await examine({...row,audit:true});assert.equal(replay.status,'dead');assert.equal(replay.nodes,row.nodes);
 }else if(row.status==='extended'){
  const sums=new Map();for(const spec of row.placements){const p=materialize(spec);for(const e of p.orientation.occupancy.values()){const key=a2Add(e.point,p.translation).join();sums.set(key,(sums.get(key)||0)+e.weight);}}
  for(const [point,value] of sums)if(value<12)assert.ok(legalAt(row.placements,point.split(',').map(Number)).size>0,`Dead checkpoint at ${point}`);
 }
}
const deadPair=[ROOT,{orientation:7,translation:[6,0,-6]}];
assert.equal((await grow({initial:deadPair,target:2,budget:120,audit:true})).result,'no','Whole-frontier failure must outrank checkpoint');
const index=report.connections.findIndex(r=>r.status==='extended'),previous=report.connections[index];
const timed=await examine({attachment:previous.attachment,target:24,budget:0});assert.equal(timed.status,'unresolved');
const revised=incorporate(report,index,timed);assert.equal(revised.connections[index].status,'extended');assert.equal(revised.connections[index].lastAttempt.status,'unresolved');assert.equal(revised.connections[index].history.length,2);assert.equal(revised.model.sampleCount,report.model.sampleCount);
assert.equal((await examine({attachment:deadPair[1],budget:0})).status,'unresolved','Budget exhaustion is never negative evidence');
console.log(JSON.stringify({passed:true,uniquePatches:signatures.size,connections:report.counts,encoding:report.encoding,retained:survivors,classes:inferred.classes,graphAudit:'all 279 dead roots replayed',checkpointAudit:'all 40 extensions independently checked'},null,2));
