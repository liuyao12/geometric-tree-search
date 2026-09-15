// Known-coordinate finite-pool comparison. Halo markings are a learned hypothesis.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
import {branchExclusionClass} from './branch-local-exclusions.mjs';
import {connectionMarkingClass,independentConnectionDomains} from './junction-connection-filter.mjs';
import {mandatoryFrontierClass} from './junction-mandatory-order.mjs';
const [compiledPath,kernelPath,dest,junctionPath,connectionPath]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
const raw=readFileSync(compiledPath),compiled=JSON.parse(raw);
const junctionRaw=readFileSync(junctionPath),junctions=JSON.parse(junctionRaw);
assert.equal(junctions.inputHash,compiled.inputHash);assert.equal(junctions.learningHash,compiled.learningHash);
const connectionRaw=readFileSync(connectionPath),connections=JSON.parse(connectionRaw);assert.equal(connections.junctionHash,hash(junctionRaw));
const {PointSearch,verify}=await import(pathToFileURL(kernelPath));
const sourceHashes=Object.fromEntries(['boron-junction-connection-search.mjs','junction-mandatory-order.mjs','junction-connection-filter.mjs','linear-frontier-decision.mjs','branch-local-exclusions.mjs'].map(n=>[n,hash(readFileSync(new URL(n,import.meta.url)))]));
function audit(e,model){
 const chosen=new Set(e.placed.keys()),totals=new Map(model.required.map(p=>[p,0])),marks=new Map();
 for(const c of model.candidates)if(chosen.has(c.id)){
  for(const x of c.t)totals.set(x.point,totals.get(x.point)+x.value);
  for(const x of c.m){const key=JSON.stringify([x.point,x.channel]);if(marks.has(key))assert.equal(marks.get(key),x.lo);marks.set(key,x.lo);}
 }
 const expected=new Map([...totals].filter(([,t])=>t<model.capacity).map(([p])=>[p,new Map()]));
 const filtered=independentConnectionDomains(e,model,e.junctionNodes,e.connectionEdges).graph;
 for(const c of model.candidates){
  const incident=[];
  if(!chosen.has(c.id)&&!e.branchBlocked?.has(c.id)&&(!filtered||c.t.every(x=>!expected.has(x.point)||filtered.get(x.point)?.has(c.id)))&&c.t.every(x=>totals.get(x.point)+x.value<=model.capacity)&&c.m.every(x=>!marks.has(JSON.stringify([x.point,x.channel]))||marks.get(JSON.stringify([x.point,x.channel]))===x.lo))
   for(const x of c.t)if(expected.has(x.point)){expected.get(x.point).set(c.id,x.value);incident.push(x.point);}
  assert.deepEqual([...e.reverse.get(c.id)].sort(),incident.sort());
 }
 assert.deepEqual([...e.graph.keys()].sort(),[...expected.keys()].sort());
 for(const [p,cs] of expected)assert.deepEqual([...e.graph.get(p)].sort(),[...cs].sort());
 e.auditGraph();
}
mkdirSync(dest);const results=[];
for(const input of compiled.models.filter(x=>[2,5].includes(x.fold)))for(const connectionMode of ['uncoupled','learned-connections']){
 const model={capacity:input.capacity,required:input.required,candidates:input.candidates.map(c=>({...c,m:c.m.filter(x=>x.channel==='0')}))};
 const nodes=junctions.folds[input.fold].nodes;
 const compileStart=performance.now(),byPoint=new Map(nodes.map(n=>[n.point,n]));
 const edges=connections.folds[input.fold].edges.map(e=>{
  if(connectionMode==='learned-connections')return e;
  const [left,right]=e.points.map(p=>byPoint.get(p));const allowedPresentStates=[];
  left.states.forEach((a,i)=>{if(a.candidates.includes(e.candidate))right.states.forEach((b,j)=>{if(b.candidates.includes(e.candidate))allowedPresentStates.push([i,j]);});});
  return {...e,allowedPresentStates};
 });
 const Engine=mandatoryFrontierClass(linearFrontierClass(branchExclusionClass(connectionMarkingClass(PointSearch,nodes,edges,model))));
 const compileSeconds=(performance.now()-compileStart)/1000;
 assert(verify(model,input.trainingSelected).complete);
 const setupStart=performance.now(),e=new Engine(model);e.junctionNodes=nodes;e.connectionEdges=edges;
 audit(e,model);const root=JSON.stringify(e.semanticState()),setupSeconds=(performance.now()-setupStart)/1000;
 const start=performance.now();let steps=0,last,mandatoryPreferencePlacements=0,lastProgress=start;
 while(steps<1000000&&performance.now()-start<100000){
  const decision=e.decision(),frontier=[...e.graph].map(([p,cs])=>({n:cs.size,g:e.points.get(p).generation}));
  if(frontier.some(x=>x.n===0))assert.equal(decision.kind,'dead');
  else if(frontier.some(x=>x.n===1))assert.equal(decision.kind,'forced');
  else if(frontier.length){assert.equal(decision.kind,'branch');assert.equal(e.points.get(decision.point).generation,Math.min(...frontier.map(x=>x.g)));}
  last=e.advance();steps++;if(last.mandatoryPreferred)mandatoryPreferencePlacements++;
  if(performance.now()-lastProgress>20000){console.log(JSON.stringify({progress:true,fold:input.fold,connectionMode,steps,selected:e.placed.size,seconds:(performance.now()-start)/1000}));lastProgress=performance.now();}
  if(steps%100===0||['complete','exhausted','unknown'].includes(last.kind))audit(e,model);
  if(['complete','exhausted','unknown'].includes(last.kind))break;
 }
 audit(e,model);const selected=[...e.placed.keys()],check=verify(model,selected);assert(check.legal);
 if(check.complete){
  const chosen=new Set(selected.map(Number)),labels=new Map(nodes.map(n=>[n.point,n.states.findIndex(s=>s.candidates.length===n.incident.filter(x=>chosen.has(x.candidate)).length&&s.candidates.every(id=>chosen.has(id)))]));
  assert([...labels.values()].every(x=>x>=0));
  for(const edge of edges)if(chosen.has(edge.candidate))assert(edge.allowedPresentStates.some(([a,b])=>a===labels.get(edge.points[0])&&b===labels.get(edge.points[1])));
 }
 const result={fold:input.fold,file:input.file,junction:true,connectionMode,ordering:'generation-tie mandatory preference',maxSteps:1000000,maxSeconds:100,mandatoryPreferencePlacements,steps,seconds:(performance.now()-start)/1000,compileSeconds,setupSeconds,connectionDiagnostics:{...e.connectionDiagnostics},
  status:check.complete?'exact finite point-cover witness':last?.kind==='exhausted'?'exhausted finite pool':'budget-unknown',
  stats:{...e.stats},selected,markOnlyPoints:[...e.points.keys()].filter(p=>!model.required.includes(p)).length};
 e.undo(0);audit(e,model);assert.equal(JSON.stringify(e.semanticState()),root);result.rootRollback=true;
 writeFileSync(`${dest}/${input.fold}-${connectionMode}.json`,JSON.stringify({compiledHash:hash(raw),junctionHash:hash(junctionRaw),connectionHash:hash(connectionRaw),kernelHash:hash(readFileSync(kernelPath)),sourceHashes,model,result}),{flag:'wx'});
 results.push({...result,selected:selected.length});console.log(JSON.stringify(results.at(-1)));
}
writeFileSync(`${dest}/summary.json`,JSON.stringify({scope:'Same bitset implementation, base pool, junction library, generation-tie policy and budget; uncoupled versus learned class-pair compatibility. Both are in-sample restricted models, not blind growth.',compiledHash:hash(raw),junctionHash:hash(junctionRaw),connectionHash:hash(connectionRaw),sourceHashes,results},null,2),{flag:'wx'});
