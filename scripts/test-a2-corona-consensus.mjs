import assert from 'node:assert/strict';
import fs from 'node:fs';
import {enumerateCoronas,pointModel,verifyCoronaPatch,coronaCore} from './experiment-a2-corona-consensus.mjs';
import {compactConsensus} from './compact-a2-corona-consensus.mjs';
import {verifyGrowth} from '../apps/3d-lattice-tiler/growth-search.js';
const line={tile:'line',rank:1,lattice:'A2',capacity:2,placementDomain:{kind:'a2_slab',index3:false},orientations:[{cells:[{pos:[0,0,0],weight:1},{pos:[1,-1,0],weight:1}],marks:[{pos:[0,0,0],component:0,value:0},{pos:[1,-1,0],component:0,value:0}]}]};
for(const radius of [1,2,3]){const result=enumerateCoronas(line,{radius});assert.equal(result.complete,true);assert.equal(result.solutions,1);assert.equal(result.patches[0].length,2*radius+1);assert.equal(result.commonValues,2*radius+2);assert.equal(result.addedValues,2*radius);assert.ok(verifyCoronaPatch(line,result.patches[0],radius).ok);}
const cutoff=enumerateCoronas(pointModel(),{radius:2,nodeLimit:1});assert.equal(cutoff.complete,false);assert.equal(cutoff.reason,'node limit');assert.throws(()=>compactConsensus(cutoff),/Incomplete/);
// Independent fixed-core enumerator for the Turtle one-corona. It uses plain
// maps, lexical point order and fresh brute-force domains, not GrowthGraph.
const model=pointModel(),root={oi:0,translation:[0,0,0]},core=model.orientations[0].cells.map(c=>c.pos.join()),seen=new Set(),solutions=new Set();
function visit(patch,totals,section){
 const state=patch.map(p=>`${p.oi}@${p.translation}`).sort().join(';');if(seen.has(state))return;seen.add(state);
 const k=[...core].sort().find(k=>(totals.get(k)??0)<12);
 if(k===undefined){if(verifyGrowth(model,patch).ok)solutions.add(state);return;}
 const at=k.split(',').map(Number),used=new Set(patch.map(p=>`${p.oi}@${p.translation}`)),tried=new Set();
 for(let oi=0;oi<model.orientations.length;oi++)for(const a of model.orientations[oi].cells){
  const t=at.map((v,i)=>v-a.pos[i]),id=`${oi}@${t}`;if(used.has(id)||tried.has(id))continue;tried.add(id);
  const o=model.orientations[oi],ts=new Map(totals),ms=new Map(section);let ok=true;
  for(const c of o.cells){const k=c.pos.map((v,i)=>v+t[i]).join(),n=(ts.get(k)??0)+c.weight;if(n>12){ok=false;break;}ts.set(k,n);}if(!ok)continue;
  for(const m of o.marks){const k=`${m.pos.map((v,i)=>v+t[i])}|${m.component}`;if(ms.has(k)&&ms.get(k)!==m.value){ok=false;break;}ms.set(k,m.value);}if(ok)visit([...patch,{oi,translation:t}],ts,ms);
 }
}
visit([root],new Map(model.orientations[0].cells.map(c=>[c.pos.join(),c.weight])),new Map(model.orientations[0].marks.map(m=>[`${m.pos}|${m.component}`,m.value])));
const one=enumerateCoronas(model,{radius:1});assert.equal(one.complete,true);assert.equal(one.solutions,73);assert.deepEqual(new Set(one.patches.map(p=>p.map(p=>`${p.oi}@${p.translation}`).sort().join(';'))),solutions);
// Independently reconstruct each glued section and its intersection. A missing
// assignment is not an assigned zero. Check every retained corona separately.
for(const file of process.argv.slice(2)){
 const r=JSON.parse(fs.readFileSync(file));assert.ok(r.complete);assert.ok(r.solutions>0);const m=pointModel({tile:r.tile,rank:r.rank,lattice:r.lattice});let intersection=null;
 assert.equal(new Set(r.patches.map(p=>p.map(p=>`${p.oi}@${p.translation}`).sort().join(';'))).size,r.solutions);
 for(const patch of r.patches){
  assert.ok(verifyCoronaPatch(m,patch,r.radius).ok);
  const section=new Map();for(const p of patch)for(const e of m.orientations[p.oi].marks){const k=`${e.pos.map((v,i)=>v+p.translation[i])}|${e.component}`;if(section.has(k))assert.ok(section.get(k)===e.value);section.set(k,e.value===0?0:e.value);}
  if(!intersection)intersection=section;else for(const [k,v] of intersection)if(!section.has(k)||section.get(k)!==v)intersection.delete(k);
 }
 assert.deepEqual([...intersection].sort(),r.support.map(e=>[`${e.point}|${e.component}`,e.value]).sort());
 // Every added assignment remains a consequence at every orientation. Check
 // accepted corona transports, including signed rank-3 / scalar rank-1 actions.
 const x=pointModel({...r,support:r.support});
 assert.ok(x.orientations.every(o=>o.marks.length===r.support.length));
 console.log(`${r.tile} ${r.lattice} radius ${r.radius}: independently replayed ${r.solutions} coronas and ${r.commonValues} common values.`);
}
console.log('PASS exact line coronas 1–3, unknown cutoff gate, independent Turtle one-corona exhaustive enumeration, and supplied corona intersections.');
