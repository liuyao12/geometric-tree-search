import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {portableCloudClass,portableState,portableWitnessCheck,cloudContains} from './portable-cloud-filter.mjs';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
const [modelPath,kernelPath,dest]=process.argv.slice(2),hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const data=JSON.parse(readFileSync(modelPath)),{PointSearch,verify}=await import(pathToFileURL(kernelPath));
const sourceHashes=Object.fromEntries(['boron-portable-search.mjs','portable-cloud-filter.mjs','linear-frontier-decision.mjs'].map(n=>[n,hash(new URL(n,import.meta.url))]));
function audit(e,model,enabled){
 const chosen=new Set(e.placed.keys()),state=portableState(model,chosen),totals=new Map(model.required.map(p=>[p,0])),scalar=new Map();assert(!state.duplicate);
 for(const c of model.candidates)if(chosen.has(c.id)){
  for(const t of c.t)totals.set(t.point,totals.get(t.point)+t.value);
  for(const m of c.m)scalar.set(JSON.stringify([m.point,m.channel??'0']),m.lo);
 }
 const graph=new Map([...totals].filter(([,v])=>v<model.capacity).map(([p])=>[p,new Map()]));
 for(const c of model.candidates){
  let allowed=!chosen.has(c.id)&&!state.owners.has(c.base)&&c.t.every(t=>totals.get(t.point)+t.value<=model.capacity)&&c.m.every(m=>!scalar.has(JSON.stringify([m.point,m.channel??'0']))||scalar.get(JSON.stringify([m.point,m.channel??'0']))===m.lo);
  if(enabled&&allowed)for(const m of c.cloudM)for(const a of state.marks.get(JSON.stringify([m.point,m.channel??'portable']))||[])if(!cloudContains(m.cloud,a,2*model.cloudRadius+1e-10))allowed=false;
  const at=[];if(allowed)for(const t of c.t)if(graph.has(t.point)){graph.get(t.point).set(c.id,t.value);at.push(t.point);}
  assert.deepEqual([...e.reverse.get(c.id)].sort(),at.sort());
 }
 assert.deepEqual([...graph.keys()].sort(),[...e.graph.keys()].sort());for(const [p,cs] of graph)assert.deepEqual([...e.graph.get(p)].sort(),[...cs].sort());
 e.auditGraph();
}
mkdirSync(dest);const results=[];
for(const input of data.models)for(const enabled of [false,true]){
 const model={...input.model,candidates:input.model.candidates.map(c=>({...c,cloudM:c.cloudM.map(m=>({...m,cloud:data.clouds[m.cloud]}))}))};
 const Engine=linearFrontierClass(portableCloudClass(PointSearch,model,{enabled}));
 const setup=performance.now(),e=new Engine(model);audit(e,model,enabled);const setupSeconds=(performance.now()-setup)/1000,root=JSON.stringify(e.semanticState());
 const start=performance.now();let steps=0,last,lastProgress=start;
 while(steps<1000000&&performance.now()-start<30000){
  const d=e.decision(),frontier=[...e.graph].map(([p,cs])=>({n:cs.size,g:e.points.get(p).generation}));
  if(frontier.some(x=>x.n===0))assert.equal(d.kind,'dead');else if(frontier.some(x=>x.n===1))assert.equal(d.kind,'forced');else if(frontier.length){assert.equal(d.kind,'branch');assert.equal(e.points.get(d.point).generation,Math.min(...frontier.map(x=>x.g)));}
  last=e.advance();steps++;
  if(steps%100===0)audit(e,model,enabled);
  if(performance.now()-lastProgress>10000){console.log(JSON.stringify({progress:true,fold:input.fold,enabled,steps,selected:e.placed.size,seconds:(performance.now()-start)/1000}));lastProgress=performance.now();}
  if(['complete','exhausted','unknown'].includes(last.kind))break;
 }
 audit(e,model,enabled);const selected=[...e.placed.keys()],selectedSet=new Set(selected),byId=new Map(model.candidates.map(c=>[c.id,c]));
 const scalarCheck=verify({...model,candidates:selected.map(id=>byId.get(id))},selected);assert(scalarCheck.legal);
 const markingCheck=enabled?portableWitnessCheck(model,selectedSet):{valid:true,status:'disabled',witnesses:[]};
 const result={fold:input.fold,file:input.file,enabled,maxSeconds:30,maxSteps:1000000,setupSeconds,seconds:(performance.now()-start)/1000,steps,stats:{...e.stats},selected,
  status:scalarCheck.complete&&markingCheck.valid?'verified finite registered filling':last?.kind==='exhausted'?'exhausted finite registered pool':last?.kind==='unknown'?'unknown-common-value':'budget-unknown',scalarComplete:scalarCheck.complete,markingStatus:markingCheck.status,commonValues:markingCheck.witnesses?.length??0};
 e.undo(0);audit(e,model,enabled);assert.equal(JSON.stringify(e.semanticState()),root);assert.equal(e.portable.owners.size,0);assert.equal(e.portable.marks.size,0);result.rootRollback=true;
 writeFileSync(`${dest}/${input.fold}-${enabled}.json`,JSON.stringify({modelHash:hash(modelPath),kernelHash:hash(kernelPath),sourceHashes,result,commonWitnesses:markingCheck.witnesses??[]}),{flag:'wx'});
 results.push({...result,selected:selected.length});console.log(JSON.stringify(results.at(-1)));
}
writeFileSync(`${dest}/summary.json`,JSON.stringify({scope:'Same finite registered variant pool and shared-placement inventory; scalar-only versus portable cloud constraints. Pairwise-disjointness relaxation feeds the reference-order frontier; common cloud values are required to certify completion. Not a complete continuous-pose search.',modelHash:hash(modelPath),kernelHash:hash(kernelPath),sourceHashes,results},null,2),{flag:'wx'});
