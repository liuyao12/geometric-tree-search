import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {capacityLookaheadClass} from './point-capacity-lookahead.mjs';
const {PointSearch}=await import(pathToFileURL(process.argv[2]));
let seed=39281,states=0,preservedCompletions=0,pruned=0;const random=n=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return (seed>>>16)%n;};
for(let trial=0;trial<80;trial++){
 const capacity=1+random(2),required=['a','b','c'],candidates=[];
 for(let i=0;i<5;i++){let t=required.filter(()=>random(2)).map(point=>({point,value:1+random(capacity)}));if(!t.length)t=[{point:required[random(3)],value:1}];candidates.push({id:`g${i}`,base:`i${i}`,t,m:[]});}
 // One duplicate geometry with shared inventory tests variant caching.
 candidates.push({...candidates[0],id:'variant'});
 const model={capacity,required,candidates,complete:true};
 class Inventory extends PointSearch{
  reason(c){return super.reason(c)||([...this.placed.keys()].some(id=>this.candidates.get(id).base===c.base)?'inventory':null);}
  refresh(changed){super.refresh(new Set(this.points.keys()));}
 }
 const E=capacityLookaheadClass(Inventory,model);
 const legal=[];for(let mask=0;mask<64;mask++){
  const rows=candidates.filter((_,i)=>mask&(1<<i)),owners=new Set(rows.map(c=>c.base)),totals=required.map(p=>rows.reduce((s,c)=>s+c.t.filter(t=>t.point===p).reduce((a,t)=>a+t.value,0),0));
  if(owners.size===rows.length&&totals.every(t=>t<=capacity))legal.push({mask,rows,complete:totals.every(t=>t===capacity)});
 }
 for(const state of legal){
  const e=new E(model),root=JSON.stringify(e.semanticState());let reachable=true;
  for(const c of state.rows){if(e.reason(e.candidates.get(c.id))){reachable=false;break;}e.apply(c.id);}
  if(!reachable){assert(!legal.some(s=>s.complete&&(s.mask&state.mask)===state.mask));continue;}
  for(let i=0;i<candidates.length;i++){
   const c=e.candidates.get(candidates[i].id);if(state.mask&(1<<i))continue;
   if(e.reason(c)==='proved-future-capacity-dead'){
    pruned++;const prefix=state.mask|(1<<i);assert(!legal.some(s=>s.complete&&(s.mask&prefix)===prefix));
   }
  }
  if(state.complete)preservedCompletions++;
  e.auditGraph();e.undo(0);e.auditGraph();assert.equal(JSON.stringify(e.semanticState()),root);states++;
 }
}
assert(pruned>0&&preservedCompletions>0);
console.log(JSON.stringify({states,preservedCompletions,pruned,status:'exhaustive finite-subset checks passed'}));
