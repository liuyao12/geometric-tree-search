// Known-coordinate finite-pool comparison. Halo markings are a learned hypothesis.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
import {branchExclusionClass} from './branch-local-exclusions.mjs';
const [compiledPath,kernelPath,dest,compoundPath]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
const raw=readFileSync(compiledPath),compiled=JSON.parse(raw);
const compoundRaw=readFileSync(compoundPath),compounds=JSON.parse(compoundRaw);
assert.equal(compounds.inputHash,compiled.inputHash);assert.equal(compounds.learningHash,compiled.learningHash);
const {PointSearch,verify}=await import(pathToFileURL(kernelPath));
const Engine=linearFrontierClass(branchExclusionClass(PointSearch));
const sourceHashes=Object.fromEntries(['boron-compound-search.mjs','linear-frontier-decision.mjs','branch-local-exclusions.mjs'].map(n=>[n,hash(readFileSync(new URL(n,import.meta.url)))]));
function audit(e,model){
 const chosen=new Set(e.placed.keys()),totals=new Map(model.required.map(p=>[p,0])),marks=new Map();
 for(const c of model.candidates)if(chosen.has(c.id)){
  for(const x of c.t)totals.set(x.point,totals.get(x.point)+x.value);
  for(const x of c.m){const key=JSON.stringify([x.point,x.channel]);if(marks.has(key))assert.equal(marks.get(key),x.lo);marks.set(key,x.lo);}
 }
 const expected=new Map([...totals].filter(([,t])=>t<model.capacity).map(([p])=>[p,new Map()]));
 for(const c of model.candidates){
  const incident=[];
  if(!chosen.has(c.id)&&!e.branchBlocked?.has(c.id)&&c.t.every(x=>totals.get(x.point)+x.value<=model.capacity)&&c.m.every(x=>!marks.has(JSON.stringify([x.point,x.channel]))||marks.get(JSON.stringify([x.point,x.channel]))===x.lo))
   for(const x of c.t)if(expected.has(x.point)){expected.get(x.point).set(c.id,x.value);incident.push(x.point);}
  assert.deepEqual([...e.reverse.get(c.id)].sort(),incident.sort());
 }
 assert.deepEqual([...e.graph.keys()].sort(),[...expected.keys()].sort());
 for(const [p,cs] of expected)assert.deepEqual([...e.graph.get(p)].sort(),[...cs].sort());
 e.auditGraph();
}
mkdirSync(dest);const results=[];
for(const input of compiled.models)for(const policy of ['baseline','cross-compound']){
 const model={capacity:input.capacity,required:input.required,candidates:input.candidates.map(c=>({...c,m:c.m.filter(x=>x.channel==='0')}))};
 const proposals=compounds.folds[input.fold].proposals.filter(p=>p.sourceFolds.some(f=>f!==input.fold)).map(p=>p.base.map(i=>String(i).padStart(6,'0')));
 assert(verify(model,input.trainingSelected).complete);
 const setupStart=performance.now(),e=new Engine(model);audit(e,model);const root=JSON.stringify(e.semanticState()),setupSeconds=(performance.now()-setupStart)/1000;
 let policyEvaluations=0,viableCompoundEvaluations=0,scores=new Map();
 e.preference=c=>scores.get(c.id)||0;
 const originalDecision=e.decision.bind(e);
 e.decision=()=>{
  scores=new Map();
  if(policy==='cross-compound'){
   policyEvaluations++;
   for(const ids of proposals){
    const pending=ids.filter(id=>!e.placed.has(id));
    if(!pending.length||pending.some(id=>e.reason(e.candidates.get(id))))continue;
    const added=new Map();
    for(const id of pending)for(const x of e.candidates.get(id).t)added.set(x.point,(added.get(x.point)||0)+x.value);
    if([...added].some(([p,v])=>e.points.get(p).total+v>model.capacity))continue;
    viableCompoundEvaluations++;
    const score=1+(ids.length-pending.length)*100+ids.length;
    for(const id of pending)scores.set(id,Math.max(scores.get(id)||0,score));
   }
  }
  return originalDecision();
 };
 const start=performance.now();let steps=0,last;
 while(steps<100000&&performance.now()-start<15000){
  const decision=e.decision(),frontier=[...e.graph].map(([p,cs])=>({n:cs.size,g:e.points.get(p).generation}));
  if(frontier.some(x=>x.n===0))assert.equal(decision.kind,'dead');
  else if(frontier.some(x=>x.n===1))assert.equal(decision.kind,'forced');
  else if(frontier.length){assert.equal(decision.kind,'branch');assert.equal(e.points.get(decision.point).generation,Math.min(...frontier.map(x=>x.g)));}
  last=e.advance();steps++;
  if(steps%100===0||['complete','exhausted','unknown'].includes(last.kind))audit(e,model);
  if(['complete','exhausted','unknown'].includes(last.kind))break;
 }
 audit(e,model);const selected=[...e.placed.keys()],check=verify(model,selected);assert(check.legal);
 const result={fold:input.fold,file:input.file,policy,steps,seconds:(performance.now()-start)/1000,setupSeconds,proposals:proposals.length,policyEvaluations,viableCompoundEvaluations,
  status:check.complete?'exact finite point-cover witness':last?.kind==='exhausted'?'exhausted finite pool':'budget-unknown',
  stats:{...e.stats},selected,markOnlyPoints:[...e.points.keys()].filter(p=>!model.required.includes(p)).length};
 e.undo(0);audit(e,model);assert.equal(JSON.stringify(e.semanticState()),root);result.rootRollback=true;
 writeFileSync(`${dest}/${input.fold}-${policy}.json`,JSON.stringify({compiledHash:hash(raw),compoundHash:hash(compoundRaw),kernelHash:hash(readFileSync(kernelPath)),sourceHashes,model,result}),{flag:'wx'});
 results.push({...result,selected:selected.length});console.log(JSON.stringify(results.at(-1)));
}
writeFileSync(`${dest}/summary.json`,JSON.stringify({scope:'Original marked finite model; baseline versus soft ordering by validated compounds observed in other configurations. No macro execution or candidate elimination. Base dictionary and t/m remain jointly fitted.',compiledHash:hash(raw),compoundHash:hash(compoundRaw),sourceHashes,results},null,2),{flag:'wx'});
