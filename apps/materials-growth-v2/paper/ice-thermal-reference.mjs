// Full frozen finite candidate pool. No MILP-selected answer supplied to search.
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const raw=readFileSync(process.argv[2]),d=JSON.parse(raw),kernelRaw=readFileSync(process.argv[3]);
const {PointSearch,verify}=await import(pathToFileURL(process.argv[3]).href);
const results=[];
for(const c of d.configurations.filter(c=>!c.training))for(const marked of [false,true]){
 const model={capacity:2,required:Array.from({length:c.atoms},(_,i)=>String(i)),candidates:c.occurrences.flatMap((o,i)=>o.matched?[{
  id:String(i).padStart(6,'0'),t:o.ids.map(p=>({point:String(p),value:1})),
  m:marked?o.permutation.flatMap((j,u)=>{const v=d.scalarLabels[d.offsets[o.type]+u];return v==null?[]:[{point:String(o.ids[j]),lo:v,hi:v}];}):[]
 }]:[])};
 const engine=new PointSearch(model),initial=JSON.stringify(engine.semanticState()),start=performance.now();let steps=0,last;
 while(steps<10000&&performance.now()-start<1000){
  const decision=engine.decision(),frontier=[...engine.graph].map(([p,cs])=>({p:engine.points.get(p),cs}));
  if(frontier.some(x=>x.cs.size===0))assert.equal(decision.kind,'dead');
  else if(frontier.some(x=>x.cs.size===1))assert.equal(decision.kind,'forced');
  else if(frontier.length){assert.equal(decision.kind,'branch');assert.equal(engine.points.get(decision.point).generation,Math.min(...frontier.map(x=>x.p.generation)));}
  last=engine.advance();steps++;
  if(steps%50===0||['complete','exhausted'].includes(last.kind))engine.auditGraph();
  if(['complete','exhausted','unknown'].includes(last.kind))break;
 }
 const selected=[...engine.placed.keys()],check=verify(model,selected),stats={...engine.stats},seconds=(performance.now()-start)/1000;
 engine.undo(0);engine.auditGraph();assert.equal(JSON.stringify(engine.semanticState()),initial);
 const r={id:c.id,marked,status:check.complete?'exact finite cover':last?.kind==='exhausted'?'exhausted finite pool':'budget unknown',
  selected,steps,seconds,stats,rootSemanticRollback:true};results.push(r);console.log(JSON.stringify({...r,selected:selected.length}));
}
writeFileSync(process.argv[4],JSON.stringify({scope:'Supplied-coordinate finite pool, all required atoms roots at generation zero; uniform t=1/2 hypothesis; no connectivity constraint or blind growth.',
 dictionaryHash:createHash('sha256').update(raw).digest('hex'),kernelHash:createHash('sha256').update(kernelRaw).digest('hex'),results}),{flag:'wx'});
