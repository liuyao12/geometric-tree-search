import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const raw=readFileSync(process.argv[2]),coords=JSON.parse(raw).configurations;
const cr=readFileSync(process.argv[3]),composition=JSON.parse(cr),d=JSON.parse(readFileSync(process.argv[4]));
assert.equal(createHash('sha256').update(raw).digest('hex'),d.coordinateHash);
assert.equal(createHash('sha256').update(cr).digest('hex'),d.compositionHash);
const results=[];
const baseRaw=process.argv[5]?readFileSync(process.argv[5]):null;
const base=baseRaw?JSON.parse(baseRaw):null;
if(baseRaw)assert.equal(createHash('sha256').update(baseRaw).digest('hex'),composition.sourceHash);
if(process.argv[6]){
 const frozen=readFileSync(process.argv[6]);assert.equal(createHash('sha256').update(frozen).digest('hex'),d.frozenDictionaryHash);
 assert.deepEqual(d.types,JSON.parse(frozen).types);
}
for(const f of d.configurations){
 const c=coords.find(x=>x.id===f.id),original=composition.configurations.find(x=>x.id===f.id),expected=new Map(original.occurrences.map(o=>[[...o.ids].sort((a,b)=>a-b).join(':'),o]));
 const totals=c.positions.map(()=>0),full=c.positions.map(()=>0),seen=new Set();let maximum=0;
 original.occurrences.forEach(o=>o.ids.forEach((p,u)=>full[p]+=o.weights[u]));assert.ok(full.every(n=>n===4));
 if(base){
  const source=base.results.find(r=>r.id===f.id),used=new Set();
  for(const o of original.occurrences){
   const counts=new Map();for(const e of o.constituentEdges){
    assert.ok(!used.has(e));used.add(e);const edge=source.componentPairs[e];assert.ok(edge);
    edge.forEach(component=>source.components[component].forEach(p=>counts.set(p,(counts.get(p)||0)+1)));
   }
   assert.equal(counts.size,o.ids.length);o.ids.forEach((p,u)=>assert.equal(counts.get(p),o.weights[u]));
  }
  assert.equal(used.size,source.componentPairs.length);
 }
 for(const o of f.occurrences){
  const key=[...o.ids].sort((a,b)=>a-b).join(':'),base=expected.get(key);assert.ok(base&&!seen.has(key));seen.add(key);
  if(!o.matched)continue;
  const t=d.types[o.type],R=o.rotationRow;assert.deepEqual([...o.permutation].sort((a,b)=>a-b),[0,1,2,3,4,5,6,7,8]);
  for(let i=0;i<3;i++)for(let j=0;j<3;j++)assert.ok(Math.abs(R[i].reduce((s,x,k)=>s+x*R[j][k],0)-(i===j?1:0))<1e-9);
  const det=R[0][0]*(R[1][1]*R[2][2]-R[1][2]*R[2][1])-R[0][1]*(R[1][0]*R[2][2]-R[1][2]*R[2][0])+R[0][2]*(R[1][0]*R[2][1]-R[1][1]*R[2][0]);assert.ok(Math.abs(det-1)<1e-9);
  c.cell.forEach((row,i)=>row.forEach((v,j)=>assert.ok(i===j||v===0)));
  t.positions.forEach((p,u)=>{
   const id=o.ids[o.permutation[u]];assert.equal(t.species[u],c.species[id]);assert.equal(t.weights[u],base.weights[base.ids.indexOf(id)]);
   const q=[0,1,2].map(k=>o.translation[k]+p.reduce((s,x,j)=>s+x*R[j][k],0));
   const residual=Math.hypot(...q.map((x,k)=>{let v=x-c.positions[id][k],L=c.cell[k][k];return v-Math.round(v/L)*L;}));
   assert.ok(residual<=d.epsilonAngstrom+1e-10);maximum=Math.max(maximum,residual);totals[id]+=t.weights[u];
  });
 }
 assert.equal(seen.size,expected.size);assert.ok(totals.every(n=>n<=4));
 const r={id:f.id,training:f.training,matched:f.matched,supports:f.supports,atoms:c.positions.length,filledByMatchedSupports:totals.filter(n=>n===4).length,maximumResidual:maximum};results.push(r);console.log(r);
}
console.log({types:d.types.length,singletons:d.types.filter(t=>t.trainingOccurrences===1).length,scope:'Matched selected supports only; missing support does not prove no alternative cover'});
