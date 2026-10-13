import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {depthPointPath,depthPointSteps} from '../apps/knot-movie/depth-point-path.mjs';
import {classifyLatticeBlind} from '../research/knot-classifier/lattice-blind-search.mjs';
import {verifyLatticeCertificate} from '../research/knot-classifier/lattice-search.mjs';
import {latticeMoves} from '../research/knot-classifier/lattice-moves.mjs';
function provider(graph){return{sourceKey:'0',targetKey:'3',version:()=>0,domain:key=>({point:key,boundary:new Map(),complete:true,candidates:graph.get(key).map(destination=>({id:`${key}:${destination}`,point:key,destination}))}),decorate:e=>({id:e.id,t:new Map([[e.point,1]]),m:new Map()}),resolve:e=>({key:e.destination})};}
let checks=0;
for(let mask=0;mask<64;mask++){
 const g=new Map(Array.from({length:4},(_,i)=>[String(i),[]]));[[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]].forEach(([a,b],i)=>{if(mask&(1<<i)){g.get(String(a)).push(String(b));g.get(String(b)).push(String(a));}});
 const distances=new Map([['0',0]]),queue=['0'];for(const k of queue)for(const n of g.get(k))if(!distances.has(n)){distances.set(n,distances.get(k)+1);queue.push(n);}
 for(let depth=0;depth<=5;depth++){
  const r=depthPointPath(provider(g),{maxDepth:depth});assert.equal(r.status,(distances.get('3')??Infinity)<=depth?'equivalent':'exhausted-finite-search');
  if(r.path){assert.ok(r.path.length<=depth);let key='0';for(const id of r.path){const [a,b]=id.split(':');assert.equal(a,key);assert.ok(g.get(a).includes(b));key=b;}assert.equal(key,'3');}checks++;
 }
}
const g=new Map([['0',['1']],['1',['0','3']],['3',['1']]]);
assert.equal(depthPointPath(provider(g),{maxDepth:2,nodeCap:0}).status,'unknown');
const steps=depthPointSteps(provider(g),{maxDepth:2});const first=steps.next();assert.equal(first.done,false);assert.equal(first.value.stats.nodes,1);
let last;do{last=steps.next();}while(!last.done);assert.equal(last.value.status,'equivalent');
const records=JSON.parse(readFileSync(new URL('../research/knot-classifier/lattice-corpus-12.json',import.meta.url))).records.filter(r=>r.crossings>=3&&r.crossings<=8);
const goal=records[0].vertices,source=latticeMoves(goal,{maxEdges:240})[0].vertices,bank=[...records.slice(1),records[0]].map(r=>({vertices:r.vertices,id:'unused',crossings:99}));
for(const learn of [false,true]){
 const r=classifyLatticeBlind({vertices:source,id:'misleading'},bank,{learn,maxDepth:1,maxMs:20000,nodeCap:1000,searchSeeds:[31,73,131,197],wholeWindowChildren:true});
 assert.equal(r.status,'identified');assert.equal(r.referenceIndex,34);assert.equal(r.referenceChecks,35);assert.equal(r.rootGraph.complete,true);assert.equal(r.certificate.steps.length,1);assert.ok(r.nodes<=1000);
 assert.equal(verifyLatticeCertificate(r.certificate),true);assert.equal(verifyLatticeCertificate(r.certificate,{shouldStop:()=>true}),false);
 const altered=structuredClone(r.certificate);altered.steps[0].afterDiagram='fabricated';assert.throws(()=>verifyLatticeCertificate(altered),/Inconsistent/);
}
const budget=classifyLatticeBlind(source,bank,{maxMs:0});assert.equal(budget.status,'unknown');assert.equal(budget.rootGraph.complete,false);
assert.throws(()=>classifyLatticeBlind(source,bank,{learn:false,rootModel:{}}),/cannot import/);
console.log(JSON.stringify({passed:true,exhaustiveDepthChecks:checks,resumable:true,fullBankLateTarget:true,labelsIgnored:true,budgetsRemainUnknown:true}));
