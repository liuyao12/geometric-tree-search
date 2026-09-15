import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {portableCloudClass,portableState,cloudConsensus,cloudContains} from './portable-cloud-filter.mjs';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
const {PointSearch}=await import(pathToFileURL(process.argv[2]));
let seed=1183,subsets=0,visited=0,complete=0;
const rand=n=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return (seed>>>8)%n;};
const cloud=x=>({vectors:[[x,0,0]],colors:[[0]]});
function legal(model,selected){
 const totals=new Map(model.required.map(p=>[p,0])),bases=new Set(),scalar=new Map(),fields=new Map();
 for(const c of model.candidates)if(selected.has(c.id)){
  if(bases.has(c.base))return false;bases.add(c.base);
  for(const t of c.t){totals.set(t.point,totals.get(t.point)+t.value);if(totals.get(t.point)>model.capacity)return false;}
  for(const m of c.m){if(scalar.has(m.point)&&scalar.get(m.point)!==m.lo)return false;scalar.set(m.point,m.lo);}
  for(const m of c.cloudM){const key=JSON.stringify([m.point,m.channel??'portable']),x=m.cloud.vectors[0][0];if(!fields.has(key))fields.set(key,[]);fields.get(key).push(x);}
 }
 return [...fields.values()].every(xs=>Math.max(...xs)-Math.min(...xs)<=2*model.cloudRadius+1e-10);
}
function audit(e,model){
 const chosen=new Set(e.placed.keys()),totals=new Map(model.required.map(p=>[p,0]));
 for(const c of model.candidates)if(chosen.has(c.id))for(const t of c.t)totals.set(t.point,totals.get(t.point)+t.value);
 const graph=new Map([...totals].filter(([,v])=>v<model.capacity).map(([p])=>[p,new Map()]));
 for(const c of model.candidates){const at=[];if(!chosen.has(c.id)&&legal(model,new Set([...chosen,c.id])))for(const t of c.t)if(graph.has(t.point)){graph.get(t.point).set(c.id,t.value);at.push(t.point);}assert.deepEqual([...e.reverse.get(c.id)].sort(),at.sort());}
 assert.deepEqual([...e.graph.keys()].sort(),[...graph.keys()].sort());for(const [p,cs] of graph)assert.deepEqual([...e.graph.get(p)].sort(),[...cs].sort());
 e.auditGraph();visited++;
 const domain=[...e.graph].map(([p,c])=>({point:p,size:c.size,generation:e.points.get(p).generation})),d=e.decision();
 if(domain.some(x=>x.size===0))assert.equal(d.kind,'dead');else if(domain.some(x=>x.size===1))assert.equal(d.kind,'forced');else if(domain.length){assert.equal(d.kind,'branch');assert.equal(e.points.get(d.point).generation,Math.min(...domain.map(x=>x.generation)));}
}
for(let trial=0;trial<150;trial++){
 const model={capacity:2,required:['a','b','c'],cloudRadius:.1,candidates:[]};
 for(let group=0;group<4;group++){
  const t=model.required.filter(()=>rand(2)).map(point=>({point,value:1+rand(2)}));if(!t.length)t.push({point:'a',value:1});
  for(let variant=0;variant<2;variant++)model.candidates.push({id:`${group}-${variant}`,base:String(group),t,m:rand(2)?[]:[{point:'scalar-only',lo:variant,hi:variant}],cloudM:[{point:rand(2)?'a':'mark-only',cloud:cloud(rand(3)*.5)}]});
 }
 let solutions=0;
 for(let mask=0;mask<2**model.candidates.length;mask++){
  subsets++;const selected=new Set(model.candidates.filter((_,i)=>mask&(1<<i)).map(c=>c.id));if(!legal(model,selected))continue;
  if(model.required.every(p=>model.candidates.filter(c=>selected.has(c.id)).reduce((s,c)=>s+(c.t.find(t=>t.point===p)?.value||0),0)===model.capacity))solutions++;
 }
 const Engine=linearFrontierClass(portableCloudClass(PointSearch,model)),e=new Engine(model);const root=JSON.stringify(e.semanticState());let last,steps=0;
 do{audit(e,model);last=e.advance();steps++;assert(steps<10000);}while(!['complete','exhausted','unknown'].includes(last.kind));
 assert.notEqual(last.kind,'unknown');assert.equal(last.kind==='complete',solutions>0);if(last.kind==='complete')complete++;
 e.undo(0);audit(e,model);assert.equal(JSON.stringify(e.semanticState()),root);assert.equal(e.portable.owners.size,0);assert.equal(e.portable.marks.size,0);
}
// A feasible common intersection missed by the heuristic remains UNKNOWN.
assert.equal(cloudConsensus([cloud(-1),cloud(.8),cloud(.8)],1).status,'unknown');
const model={capacity:1,required:['a','b','c'],cloudRadius:1,candidates:[-1,.8,.8].map((x,i)=>({id:String(i),base:String(i),t:[{point:['a','b','c'][i],value:1}],m:[],cloudM:[{point:'outside',cloud:cloud(x)}]}))};
const Engine=portableCloudClass(PointSearch,model),e=new Engine(model);for(let i=0;i<3;i++)e.apply(String(i));assert.equal(e.decision().kind,'unknown');assert.equal(e.placed.size,3);
// Disjoint marked variants of the same placement cannot stack, even when t fits.
const inv={capacity:2,required:['a'],cloudRadius:.1,candidates:[0,1].map(i=>({id:String(i),base:'same-pose',t:[{point:'a',value:1}],m:[],cloudM:[]}))};
const I=portableCloudClass(PointSearch,inv),ie=new I(inv);ie.apply('0');assert.equal(ie.reason(ie.candidates.get('1')),'shared-placement-inventory');assert.equal(ie.decision().kind,'dead');ie.undo(0);assert.equal(ie.graph.get('a').size,2);
// The pair rejection bound includes the membership guards on BOTH clouds.
const edge={capacity:1,required:['a','b'],cloudRadius:.1,candidates:[0,.20000000015].map((x,i)=>({id:String(i),base:String(i),t:[{point:['a','b'][i],value:1}],m:[],cloudM:[{point:'outside',cloud:cloud(x)}]}))};
const E=portableCloudClass(PointSearch,edge),ee=new E(edge);ee.apply('0');assert.equal(ee.reason(ee.candidates.get('1')),null);ee.apply('1');
assert(edge.candidates.every(c=>cloudContains(c.cloudM[0].cloud,cloud(.100000000075),.1)));
assert.equal(ee.decision().kind,'unknown'); // The incomplete proposer may miss this guarded witness, but must not prune it.
console.log(JSON.stringify({models:150,subsets,visited,completedModels:complete,graphAndRollback:true,priorityChecks:true,unknownNotPruned:true,sharedPlacementInventory:true,twoSidedNumericalGuard:true}));
