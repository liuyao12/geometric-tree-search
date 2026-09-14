// Finite model control. Marked variants plus both expanded and collapsed baselines.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const [input,kernel,dest]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
const {PointSearch,verify}=await import(pathToFileURL(kernel));mkdirSync(dest);const results=[];
function audit(e,model){
 const selected=new Set(e.placed.keys()),byId=new Map(model.candidates.map(c=>[c.id,c])),totals=new Map(model.required.map(p=>[p,0])),marks=new Map(),used=new Set();
 for(const id of selected){const c=byId.get(id);assert(!used.has(c.inventory));used.add(c.inventory);
  for(const x of c.t)totals.set(x.point,totals.get(x.point)+x.value);
  for(const x of c.m){if(marks.has(x.point))assert.equal(marks.get(x.point),x.lo);marks.set(x.point,x.lo);}
 }
 const expected=new Map([...totals].filter(([,v])=>v<model.capacity).map(([p])=>[p,new Map()]));
 for(const c of model.candidates){const incident=[];
  if(!selected.has(c.id)&&!used.has(c.inventory)&&c.t.every(x=>totals.get(x.point)+x.value<=model.capacity)&&c.m.every(x=>!marks.has(x.point)||marks.get(x.point)===x.lo))
   for(const x of c.t)if(expected.has(x.point)){expected.get(x.point).set(c.id,x.value);incident.push(x.point);}
  assert.deepEqual([...e.reverse.get(c.id)].sort(),incident.sort());
 }
 assert.deepEqual([...e.graph.keys()].sort(),[...expected.keys()].sort());
 for(const [p,cs] of expected)assert.deepEqual([...e.graph.get(p)].sort(),[...cs].sort());
 for(const [p,v] of totals)assert.equal(e.points.get(p).total,v);
}
for(let fold=0;fold<6;fold++){
 const raw=readFileSync(`${input}/${fold}.json`),data=JSON.parse(raw);
 for(const lane of ['unmarked-collapsed','unmarked-expanded','marked']){
  const seen=new Set();const candidates=data.model.candidates.filter(c=>{
   if(lane!=='unmarked-collapsed')return true;if(seen.has(c.inventory))return false;seen.add(c.inventory);return true;
  }).map(c=>({...c,m:lane==='marked'?c.m:[]}));
  const model={...data.model,candidates};
  const e=new PointSearch({...model,constraint:(c,engine)=>{
   for(const id of engine.placed.keys())if(engine.candidates.get(id).inventory===c.inventory)return 'same-base-placement';return null;
  }});const root=JSON.stringify(e.semanticState());let steps=0,last;const start=performance.now();
  while(steps<100000&&performance.now()-start<15000){
   const decision=e.decision(),frontier=[...e.graph].map(([p,cs])=>({p:e.points.get(p),count:cs.size}));
   if(frontier.some(x=>x.count===0))assert.equal(decision.kind,'dead');
   else if(frontier.some(x=>x.count===1))assert.equal(decision.kind,'forced');
   else if(frontier.length){assert.equal(decision.kind,'branch');assert.equal(e.points.get(decision.point).generation,Math.min(...frontier.map(x=>x.p.generation)));}
   last=e.advance();steps++;
   if(steps%100===0||['complete','exhausted'].includes(last.kind)){e.auditGraph();audit(e,model);}
   if(['complete','exhausted','unknown'].includes(last.kind))break;
  }
  const ids=[...e.placed.keys()],check=verify(model,ids);assert(check.legal);
  const status=check.complete?'exact finite point-cover witness':last?.kind==='exhausted'?'exhausted declared finite model':'budget-unknown';
  const result={fold,heldOut:data.summary.heldOut,lane,status,steps,seconds:(performance.now()-start)/1000,
   candidates:candidates.length,selected:ids,stats:{...e.stats}};
  e.undo(0);audit(e,model);assert.equal(JSON.stringify(e.semanticState()),root);result.rootSemanticRollback=true;
  writeFileSync(`${dest}/${fold}-${lane}.json`,JSON.stringify({inputHash:hash(raw),model,result}),{flag:'wx'});
  results.push({...result,selected:ids.length});console.log(JSON.stringify(results.at(-1)));
 }
}
writeFileSync(`${dest}/summary.json`,JSON.stringify({scope:'Known-coordinate finite point models; learned context variants; no continuous completeness or blind growth',kernelHash:hash(readFileSync(kernel)),results},null,2),{flag:'wx'});
