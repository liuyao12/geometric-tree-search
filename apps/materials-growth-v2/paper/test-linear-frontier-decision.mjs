import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
import {branchExclusionClass} from './branch-local-exclusions.mjs';
const {PointSearch}=await import(pathToFileURL(process.argv[2]));
let seed=76149,checks=0,steps=0;
const random=n=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed%n;};
for(let trial=0;trial<160;trial++){
 const capacity=1+random(3),n=3+random(5);
 const candidates=Array.from({length:8},(_,i)=>({id:String(i),t:Array.from({length:n},(_,p)=>p).filter(()=>random(3)===0).map(p=>({point:String(p),value:1+random(capacity)})),
  m:random(2)?[{point:'mark-only',channel:String(random(2)),lo:random(2),hi:2}]:[],score:random(3)})).filter(c=>c.t.length);
 const model={capacity,required:Array.from({length:n},(_,p)=>String(p)),candidates,preference:c=>c.score};
 for(const Parent of [PointSearch,branchExclusionClass(PointSearch)]){
  const a=new Parent(model),b=new (linearFrontierClass(Parent))(model),root=JSON.stringify(a.semanticState());
  for(let step=0;step<300;step++){
   assert.deepEqual(b.decision(),a.decision());checks++;
   const x=a.advance(),y=b.advance();assert.deepEqual(y,x);steps++;
   assert.deepEqual(b.semanticState(),a.semanticState());assert.deepEqual(b.stats,a.stats);
   a.auditGraph();b.auditGraph();
   if(['complete','unknown','exhausted'].includes(x.kind))break;
  }
  a.undo(0);b.undo(0);assert.equal(JSON.stringify(a.semanticState()),root);assert.deepEqual(b.semanticState(),a.semanticState());
 }
 // Separate synthetic scheduler states exercise generations, incomplete
 // domains, Infinity and insertion-order ties not present in all-root models.
 const a=new PointSearch(model),b=new (linearFrontierClass(PointSearch))(model);
 for(let trial=0;trial<20;trial++){
  a.graph.clear();b.graph.clear();
  for(const [id,p] of a.points){
   const generation=random(5)===0?Infinity:random(4),complete=!!random(2);
   p.generation=generation;p.complete=complete;Object.assign(b.points.get(id),{generation,complete});
   const cs=new Map(candidates.filter(()=>random(2)).map(c=>[c.id,1]));
   a.graph.set(id,cs);b.graph.set(id,new Map(cs));
  }
  assert.deepEqual(b.decision(),a.decision());checks++;
 }
}
console.log(JSON.stringify({models:160,decisionChecks:checks,lockstepAdvances:steps,markOnly:true,rollback:true,syntheticGenerations:true}));
