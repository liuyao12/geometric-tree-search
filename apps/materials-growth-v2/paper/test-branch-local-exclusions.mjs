import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {branchExclusionClass} from './branch-local-exclusions.mjs';
import {residualCapacityClass,independentResidualDomains} from './residual-capacity-filter.mjs';
const {PointSearch,verify}=await import(pathToFileURL(process.argv[2]));
let state=19;const rand=n=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return (state>>>8)%n;};
let checked=0,failedChoices=0;
for(let trial=0;trial<150;trial++){
 const model={capacity:3,required:['a','b','c'],candidates:Array.from({length:8},(_,i)=>({id:String(i),
  t:['a','b','c'].filter(()=>rand(2)).map(point=>({point,value:1+rand(3)}))})).filter(c=>c.t.length)};
 const solutions=[];
 for(let mask=0;mask<(1<<model.candidates.length);mask++){
  const ids=model.candidates.filter((_,i)=>mask&(1<<i)).map(c=>c.id);if(verify(model,ids).complete)solutions.push(ids);
 }
 for(const capacity of [false,true]){
  const Engine=branchExclusionClass(capacity?residualCapacityClass(PointSearch):PointSearch),e=new Engine(model),root=JSON.stringify(e.semanticState());let terminal=false;
  for(let step=0;step<5000;step++){
   checked++;e.auditGraph();
   for(const solution of solutions)if([...e.placed.keys()].every(id=>solution.includes(id)))
    for(const id of solution)assert(!e.branchBlocked?.has(id)&&!e.capacityBlocked?.has(id),'Removed a real completion in this prefix');
   if(capacity){const canonical=g=>JSON.stringify([...g].map(([p,cs])=>[p,[...cs].sort()]).sort());assert.equal(canonical(e.graph),canonical(independentResidualDomains(e,model)));}
   const d=e.advance();if(d.kind==='excluded')failedChoices++;
   if(['complete','exhausted'].includes(d.kind)){assert.equal(d.kind==='complete',solutions.length>0);terminal=true;break;}
  }
  assert(terminal);e.undo(0);assert.equal(JSON.stringify(e.semanticState()),root);
 }
}
assert(failedChoices>0);console.log(JSON.stringify({models:150,variants:2,checkedStates:checked,verifiedFailedChoices:failedChoices,completionPreservation:true,rootRollback:true}));
