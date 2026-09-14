// Reference scheduler on declared finite observed pools; not blind growth.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const [poolDir,markDir,selectionDir,kernelPath,dest,fixedUniverseDir]=process.argv.slice(2);
const hash=b=>createHash('sha256').update(b).digest('hex');
const {PointSearch,verify}=await import(pathToFileURL(kernelPath));mkdirSync(dest);
const results=[];
function independentAudit(engine,model){
 const byId=new Map(model.candidates.map(c=>[c.id,c])),selected=new Set(engine.placed.keys()),totals=new Map(model.required.map(p=>[p,0])),marks=new Map(),inventory=new Set();
 for(const id of selected){const c=byId.get(id);inventory.add(c.inventory);
  for(const x of c.t)totals.set(x.point,totals.get(x.point)+x.value);
  for(const x of c.m){if(marks.has(x.point))assert.equal(marks.get(x.point),x.lo);marks.set(x.point,x.lo);}
 }
 const expected=new Map([...totals].filter(([,n])=>n<model.capacity).map(([p])=>[p,new Map()]));
 for(const c of model.candidates){
  const legal=!selected.has(c.id)&&!inventory.has(c.inventory)&&c.t.every(x=>totals.get(x.point)+x.value<=model.capacity)&&c.m.every(x=>!marks.has(x.point)||marks.get(x.point)===x.lo);
  const incident=[];
  if(legal)for(const x of c.t)if(expected.has(x.point)){expected.get(x.point).set(c.id,x.value);incident.push(x.point);}
  assert.deepEqual([...engine.reverse.get(c.id)].sort(),incident.sort());
 }
 assert.deepEqual([...engine.graph.keys()].sort(),[...expected.keys()].sort());
 for(const [p,cs] of expected)assert.deepEqual([...engine.graph.get(p)].sort(),[...cs].sort());
 for(const [p,total] of totals)assert.equal(engine.points.get(p).total,total);
}
for(let fold=0;fold<6;fold++){
 const raw=readFileSync(`${poolDir}/${fold}.json`),pool=JSON.parse(raw),mr=readFileSync(`${markDir}/${fold}.json`),marks=JSON.parse(mr);
 const sr=readFileSync(`${selectionDir}/${fold}.json`),selection=JSON.parse(sr);
 assert.equal(marks.trainingDictionaryHash,pool.frozenDictionaryHash);assert.equal(marks.selectedArtifactHash,hash(sr));
 const fixedIds=fixedUniverseDir?new Set(JSON.parse(readFileSync(`${fixedUniverseDir}/${fold}-false.json`)).model.candidates.map(c=>c.id)):null;
 const capacity=selection.summary.learnedDenominator,seen=new Set(),base=[];
 for(const [index,o] of pool.testConfiguration.occurrences.entries()){
  const candidateId=String(index).padStart(6,'0');if(fixedIds&&!fixedIds.has(candidateId))continue;
  const inventory=JSON.stringify([o.type,[...o.ids].sort((a,b)=>a-b)]);
  const m=o.permutation.flatMap((p,u)=>marks.labels[3*o.type+u]===null?[]:[{point:String(o.ids[p]),lo:marks.labels[3*o.type+u],hi:marks.labels[3*o.type+u]}]).sort((a,b)=>a.point.localeCompare(b.point));
  const identity=JSON.stringify([inventory,m]);if(!fixedIds&&seen.has(identity))continue;seen.add(identity);
  base.push({id:candidateId,inventory,m,t:o.ids.map(p=>({point:String(p),value:1}))});
 }
 if(fixedIds)assert.equal(base.length,fixedIds.size);
 for(const marked of [false,true]){
  const candidates=base.map(c=>({...c,m:marked?c.m:[]}));
  const model={capacity,required:Array.from({length:pool.testConfiguration.atoms},(_,i)=>String(i)),candidates};
  // Role variants share one declared base-placement inventory identity.
  // Shared inventory entails shared t-support, so normal dependency closure suffices.
  const engine=new PointSearch({...model,constraint:(c,e)=>{
   for(const id of e.placed.keys())if(e.candidates.get(id).inventory===c.inventory)return 'same-base-placement';return null;
  }});
  const initial=JSON.stringify(engine.semanticState()),start=performance.now();let steps=0,last;
  while(steps<100000 && performance.now()-start<15000){
   const decision=engine.decision(),frontier=[...engine.graph].map(([id,c])=>({point:engine.points.get(id),count:c.size}));
   if(frontier.some(x=>x.count===0))assert.equal(decision.kind,'dead');
   else if(frontier.some(x=>x.count===1))assert.equal(decision.kind,'forced');
   else if(frontier.length){assert.equal(decision.kind,'branch');assert.equal(engine.points.get(decision.point).generation,Math.min(...frontier.map(x=>x.point.generation)));}
   last=engine.advance();steps++;
   if(steps%100===0||['complete','exhausted'].includes(last.kind)){engine.auditGraph();independentAudit(engine,model);}
   if(['complete','exhausted','unknown'].includes(last.kind))break;
  }
  const selected=[...engine.placed.keys()],check=verify(model,selected),stats={...engine.stats};
  assert(check.legal);assert.equal(new Set(selected.map(id=>engine.candidates.get(id).inventory)).size,selected.length);
  const status=check.complete?'exact finite point-cover witness':last?.kind==='exhausted'?'exhausted declared finite model':'budget-unknown';
  const seconds=(performance.now()-start)/1000;engine.undo(0);engine.auditGraph();independentAudit(engine,model);assert.equal(JSON.stringify(engine.semanticState()),initial);
  const r={fold,heldOut:pool.summary.heldOut,marked,status,candidates:candidates.length,required:model.required.length,capacity,
    steps,seconds,selected,stats,rootSemanticRollback:true};results.push(r);
  writeFileSync(`${dest}/${fold}-${marked}.json`,JSON.stringify({poolHash:hash(raw),markHash:hash(mr),selectionHash:hash(sr),model,result:r}),{flag:'wx'});
  console.log(JSON.stringify({...r,selected:selected.length}));
 }
}
writeFileSync(`${dest}/summary.json`,JSON.stringify({scope:'Declared finite point-model search; known target poses; learned scalar hypotheses; shared base-placement inventory; no continuous completeness',kernelHash:hash(readFileSync(kernelPath)),results:results.map(({selected,...r})=>({...r,selected:selected.length}))},null,2),{flag:'wx'});
