// Binary decorated variants restrict the projected physical-cover problem.
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const raw=readFileSync(process.argv[2]),d=JSON.parse(raw),mr=readFileSync(process.argv[3]),m=JSON.parse(mr);
const {PointSearch:BaseSearch,verify}=await import(pathToFileURL(process.argv[4]).href);assert(m.allContrastFeasible);
const mode=process.argv[6]||'expanded';assert(['expanded','quotient'].includes(mode));let PointSearch=BaseSearch;
if(mode==='quotient'){const {binaryQuotientClass}=await import('./binary-marking-quotient.mjs');PointSearch=binaryQuotientClass(BaseSearch);}
const results=[];
for(const c of d.configurations){
 const model={capacity:2,required:Array.from({length:c.atoms},(_,i)=>String(i)),candidates:c.occurrences.flatMap((o,i)=>{
  if(!o.matched)return [];assert(m.ports[o.type]);
  if(mode==='quotient')return [{id:String(i).padStart(6,'0'),t:o.ids.map(p=>({point:String(p),value:1})),
    xor:o.permutation.map((j,u)=>({point:String(o.ids[j]),bit:m.ports[o.type][u]*m.contrasts[o.type]})),m:[]}];
  return [0,1].map(flip=>({id:`${String(i).padStart(6,'0')}:${flip}`,
   t:o.ids.map(p=>({point:String(p),value:1})),m:o.permutation.map((j,u)=>{const value=flip^(m.ports[o.type][u]*m.contrasts[o.type]);return {point:String(o.ids[j]),lo:value,hi:value};})}));
 })};
 const e=new PointSearch(model),initial=JSON.stringify(e.semanticState()),start=performance.now();let steps=0,last;
 while(steps<10000&&performance.now()-start<1000){
  const decision=e.decision(),frontier=[...e.graph].map(([p,cs])=>({p:e.points.get(p),cs}));
  if(frontier.some(x=>!x.cs.size))assert.equal(decision.kind,'dead');
  else if(frontier.some(x=>x.cs.size===1))assert.equal(decision.kind,'forced');
  else if(frontier.length){assert.equal(decision.kind,'branch');assert.equal(e.points.get(decision.point).generation,Math.min(...frontier.map(x=>x.p.generation)));}
  last=e.advance();steps++;if(steps%50===0||['complete','exhausted'].includes(last.kind))e.auditGraph();
  if(['complete','exhausted','unknown'].includes(last.kind))break;
 }
 const selected=[...e.placed.keys()],check=verify(model,selected),stats={...e.stats};
 assert.equal(new Set(selected.map(x=>x.split(':')[0])).size,selected.length);
 const r={id:c.id,selected,steps,seconds:(performance.now()-start)/1000,stats,status:check.complete?'exact finite cover':last?.kind==='exhausted'?'exhausted decorated pool':'budget unknown'};
 e.undo(0);e.auditGraph();assert.equal(JSON.stringify(e.semanticState()),initial);results.push(r);console.log(JSON.stringify({...r,selected:selected.length}));
}
writeFileSync(process.argv[5],JSON.stringify({mode,dictionaryHash:createHash('sha256').update(raw).digest('hex'),markingHash:createHash('sha256').update(mr).digest('hex'),results,
 scope:'Binary decorated marking hypothesis, expanded variants or exact existential quotient; exact t=1/2, fixed observed candidates, all roots generation zero. Not a same-solution-set comparison to unmarked tiling or blind growth.'}),{flag:'wx'});
