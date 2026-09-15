// Known-coordinate finite-pool comparison. Halo markings are a learned hypothesis.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
import {branchExclusionClass} from './branch-local-exclusions.mjs';
const [compiledPath,kernelPath,dest]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
const raw=readFileSync(compiledPath),compiled=JSON.parse(raw);
const {PointSearch,verify}=await import(pathToFileURL(kernelPath));
const Engine=linearFrontierClass(branchExclusionClass(PointSearch));
const sourceHashes=Object.fromEntries(['boron-halo-search.mjs','linear-frontier-decision.mjs','branch-local-exclusions.mjs'].map(n=>[n,hash(readFileSync(new URL(n,import.meta.url)))]));
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
for(const input of compiled.models)for(const halo of [false,true]){
 const model={capacity:input.capacity,required:input.required,candidates:input.candidates.map(c=>({...c,m:c.m.filter(x=>halo||x.channel==='0')}))};
 assert(verify(model,input.trainingSelected).complete);
 const setupStart=performance.now(),e=new Engine(model);audit(e,model);const root=JSON.stringify(e.semanticState()),setupSeconds=(performance.now()-setupStart)/1000;
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
 const result={fold:input.fold,file:input.file,halo,steps,seconds:(performance.now()-start)/1000,setupSeconds,
  status:check.complete?'exact finite point-cover witness':last?.kind==='exhausted'?'exhausted finite pool':'budget-unknown',
  stats:{...e.stats},selected,markOnlyPoints:[...e.points.keys()].filter(p=>!model.required.includes(p)).length};
 e.undo(0);audit(e,model);assert.equal(JSON.stringify(e.semanticState()),root);result.rootRollback=true;
 writeFileSync(`${dest}/${input.fold}-${halo}.json`,JSON.stringify({compiledHash:hash(raw),kernelHash:hash(readFileSync(kernelPath)),sourceHashes,model,result}),{flag:'wx'});
 results.push({...result,selected:selected.length});console.log(JSON.stringify(results.at(-1)));
}
writeFileSync(`${dest}/summary.json`,JSON.stringify({scope:'Fixed observed poses and all-root finite target; original versus original-plus-halo; not blind growth or guaranteed solution-set equivalence.',compiledHash:hash(raw),sourceHashes,results},null,2),{flag:'wx'});
