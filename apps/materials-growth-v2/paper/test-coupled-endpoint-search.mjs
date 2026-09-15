import assert from 'node:assert/strict';
import {CoupledEndpointDomain,CoupledEndpointSearch} from './coupled-endpoint-search.mjs';
const d=new CoupledEndpointDomain(3,3),root=d.snapshot();
assert.equal(d.count,3n);d.setAllowed(0,[0,1]);d.setAllowed(1,[1,2]);
assert.equal(d.count,1n);assert.deepEqual(d.sole(),[1,1]);assert(!d.has(0,2));
d.forbid(1,1);assert.equal(d.count,0n);d.undo(0);assert.deepEqual(d.snapshot(),root);
assert.throws(()=>new CoupledEndpointDomain(2,3));
const permuted=new CoupledEndpointDomain(2,3,[[0,2],[1,0]]);
assert.deepEqual([...permuted.values()],[[0,2],[1,0]]);permuted.setAllowed(1,[0]);
assert.deepEqual([...permuted.endpointIndices(0)],[1]);assert.deepEqual(permuted.sole(),[1,0]);
let seed=18722,states=0,solutions=0;
const random=n=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed%n;};
for(let trial=0;trial<100;trial++){
 const model={capacity:2,required:['a','b','c'],blocks:[]};
 for(let i=0;i<5;i++){
  const a=random(3),b=(a+1+random(2))%3,points=[model.required[a],model.required[b]];
  model.blocks.push({id:String(i),inventory:String(random(4)),t:points.map(point=>({point,value:1})),markPoints:points,endpointChoices:[[random(2),random(2)],[random(2),random(2)]]});
 }
 const records=model.blocks.flatMap((b,i)=>b.endpointChoices.flatMap((cs,s)=>cs.map((_,j)=>[i,s,j])));
 const neighbors=records.map(([i,s,j])=>records.flatMap(([k,t,l],n)=>model.blocks[i].inventory!==model.blocks[k].inventory&&model.blocks[i].markPoints[s]===model.blocks[k].markPoints[t]&&model.blocks[i].endpointChoices[s][j]===model.blocks[k].endpointChoices[t][l]?[n]:[]));
 const e=new CoupledEndpointSearch(model,{partnerIndex:process.argv.includes('--indexed')?{records,neighbors}:null}),all=e.blocks.flatMap(b=>[0,1].map(i=>({id:e.candidateId(b.index,i,i),b,i,marks:b.markPoints.map((p,s)=>[p,b.endpointChoices[s][i]])})));
 const snapshot=()=>JSON.stringify({points:[...e.points],domains:e.blocks.map(b=>b.domain.snapshot()),owners:[...e.owners],placed:[...e.placed]});
 const initial=snapshot();
 function audit(){
  const live=new Set(all.filter(c=>!e.owners.has(c.b.inventory)&&c.b.t.every(t=>e.points.get(t.point).total+1<=2)&&c.marks.every(([p,v])=>e.points.get(p).marks.every(a=>a.value===v))).map(c=>c.id));
  let changed;
  do{changed=false;for(const c of all)if(live.has(c.id))for(const [p,v] of c.marks){
   if(e.points.get(p).total===0&&!all.some(o=>live.has(o.id)&&o.b.inventory!==c.b.inventory&&o.marks.some(([q,w])=>q===p&&w===v))){live.delete(c.id);changed=true;break;}
  }}while(changed);
  for(const c of all)assert.equal(c.b.domain.has(c.i,c.i),live.has(c.id));
  for(const p of model.required){const expected=all.filter(c=>live.has(c.id)&&c.b.t.some(t=>t.point===p)).map(c=>c.id).sort();assert.deepEqual([...e.candidateIds(p)].sort(),e.points.get(p).total<2?expected:[]);}
  states++;
 }
 audit();let found=0;
 for(let code=0;code<243;code++){
  let n=code,legal=true;const chosen=[],owners=new Set(),totals={a:0,b:0,c:0},marks=new Map();
  for(let b=0;b<5;b++){const v=n%3;n=Math.floor(n/3);if(!v)continue;const c=all[2*b+v-1];chosen.push(c);if(owners.has(c.b.inventory))legal=false;owners.add(c.b.inventory);for(const t of c.b.t)totals[t.point]++;for(const [p,m] of c.marks){if(marks.has(p)&&marks.get(p)!==m)legal=false;marks.set(p,m);}}
  if(!legal||Object.values(totals).some(t=>t!==2))continue;
  found++;solutions++;for(const c of chosen){assert(c.b.domain.has(c.i,c.i));e.apply(c.id);audit();}assert.equal(e.decision().kind,'complete');e.undo(0);assert.equal(snapshot(),initial);audit();
 }
 let last;for(let step=0;step<10000;step++){last=e.advance();audit();if(['complete','exhausted','unknown'].includes(last.kind))break;}
 assert.equal(last.kind,found?'complete':'exhausted');e.undo(0);assert.equal(snapshot(),initial);audit();
}
assert(solutions>0);console.log(JSON.stringify({models:100,indexed:process.argv.includes('--indexed'),fullSelections:24300,states,solutions,independentDomains:true,rollback:true,dfsOutcomesMatch:true}));
