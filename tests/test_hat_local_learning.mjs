import assert from 'node:assert/strict';import fs from 'node:fs';
import {HAT,ORIENTATIONS,attachments,encode,verifyPatch,canonicalPatch,grow,materialize} from '../assets/hat-local-learning.js';
import {A2_SYMMETRIES,a2Transform,a2Add,solveA2Tiling,makeHexBoundary,NoA2Marking} from '../assets/a2-tiling-engine.js';
globalThis.requestAnimationFrame=callback=>setTimeout(callback,0);
const report=JSON.parse(fs.readFileSync(new URL('../assets/data/hat-local-patches.json',import.meta.url)));
const signatures=new Set();for(const sample of [...report.training,...report.test]){assert.equal(verifyPatch(sample.placements).tiles,12);assert.ok(sample.placements.some(p=>p.orientation===sample.attachment.orientation&&p.translation.join()===sample.attachment.translation.join()));assert.ok(sample.placements.some(p=>p.orientation===0&&p.translation.join()==='0,0,0'));const signature=canonicalPatch(sample.placements);assert.ok(!signatures.has(signature));signatures.add(signature);assert.equal(signature,sample.canonical);}
const inferred=encode(report.training);assert.deepEqual(inferred,report.model);assert.equal(report.training.length,16);assert.equal(report.test.length,8);assert.ok(report.test.every(s=>verifyPatch(s.placements,inferred.support).compatible));
const independent=new Set();
const root=[...HAT.occupancy.values()],xs=root.map(e=>e.point[0]),ys=root.map(e=>e.point[1]);
for(const o of ORIENTATIONS){const points=[...o.occupancy.values()],ox=points.map(e=>e.point[0]),oy=points.map(e=>e.point[1]);for(let x=Math.min(...xs)-Math.max(...ox);x<=Math.max(...xs)-Math.min(...ox);x++)for(let y=Math.min(...ys)-Math.max(...oy);y<=Math.max(...ys)-Math.min(...oy);y++){
 if(o.index===0&&x===0&&y===0)continue;const translation=[x,y,-x-y];let contact=false,valid=true;
 for(const e of points){const at=a2Add(e.point,translation).join(','),prior=HAT.occupancy.get(at);if(prior){contact=true;if(prior.weight+e.weight>12)valid=false;}}
 if(contact&&valid)independent.add(`${o.index}:${translation}`);
}}
assert.deepEqual(new Set(attachments().map(p=>`${p.orientation}:${p.translation}`)),independent);assert.equal(independent.size,320);
const survivors=attachments().filter(p=>verifyPatch([{orientation:0,translation:[0,0,0]},p],inferred.support).compatible).length;assert.equal(survivors,58);
for(const sym of A2_SYMMETRIES){const transformed=report.test[0].placements.map(spec=>{const p=materialize(spec),old=p.orientation.symmetry;const sign=sym.sign*old.sign,permutation=sym.permutation.map(j=>old.permutation[j]);const orientation=ORIENTATIONS.find(o=>o.symmetry.sign===sign&&o.symmetry.permutation.every((v,i)=>v===permutation[i])).index;return{orientation,translation:a2Add(a2Transform(spec.translation,sym),[4,-3,-1])};});assert.equal(canonicalPatch(transformed),report.test[0].canonical);assert.equal(verifyPatch(transformed,inferred.support).compatible,true);}
assert.throws(()=>verifyPatch([...report.test[0].placements,report.test[0].placements[0]]));
// This t-legal pair has a global dead frontier. It must not be silently
// replaced by another attachment, as the original provisional-prefix API permits.
const fixed=await grow({initial:[{orientation:0,translation:[0,0,0]},{orientation:7,translation:[6,0,-6]}],seed:3974,target:12,budget:120});assert.equal(fixed.result,'no');assert.equal(fixed.placements.length,2);assert.equal(fixed.nodes,0);
const provisional=await solveA2Tiling({boundary:makeHexBoundary(10),tiles:['hat'],maximize:true,targetPlacements:12,nodeLimit:120,randomSeed:3974,marking:new NoA2Marking(),initialPlacements:[materialize({orientation:0,translation:[0,0,0]}),materialize({orientation:7,translation:[6,0,-6]})]});assert.equal(provisional.result,'yes');assert.ok(!provisional.placements.some(p=>p.orientation.index===7&&p.translation.join()==='6,0,-6'));
const audited=await grow({seed:7,support:inferred.support,target:12,budget:150,audit:true});assert.equal(audited.result,'yes');assert.equal(audited.verification.compatible,true);
console.log(JSON.stringify({passed:true,uniquePatches:signatures.size,training:16,heldOut:8,initialAttachments:320,retained:survivors,classes:inferred.classes,nonzero:inferred.nonzero,graphAudit:true},null,2));
