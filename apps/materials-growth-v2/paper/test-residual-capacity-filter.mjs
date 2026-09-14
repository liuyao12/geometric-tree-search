import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {residualCapacityClass,independentResidualDomains} from './residual-capacity-filter.mjs';
const {PointSearch,verify}=await import(pathToFileURL(process.argv[2]));const Filtered=residualCapacityClass(PointSearch);
const canon=g=>JSON.stringify([...g].map(([p,cs])=>[p,[...cs].sort()]).sort());
const model={capacity:4,required:['a','b'],candidates:[
 {id:'bad',t:[{point:'a',value:1},{point:'b',value:1}]},
 {id:'a2',t:[{point:'a',value:2}]},{id:'a2b',t:[{point:'a',value:2}]},
 {id:'b4',t:[{point:'b',value:4}]}]};
const e=new Filtered(model);assert(e.capacityBlocked.has('bad'));assert.equal(e.decision().kind,'forced');
let random=17;const rand=n=>{random=(Math.imul(random,1664525)+1013904223)>>>0;return (random>>>8)%n;};
let states=0;
for(let trial=0;trial<50;trial++){
 const m={capacity:4,required:['a','b','c'],candidates:Array.from({length:7},(_,i)=>({id:String(i),
  t:['a','b','c'].filter(()=>rand(2)).map(point=>({point,value:1+rand(4)}))})).filter(c=>c.t.length)};
 const N=m.candidates.length,solutions=[];
 for(let mask=0;mask<(1<<N);mask++){const ids=m.candidates.filter((_,i)=>mask&(1<<i)).map(c=>c.id);if(verify(m,ids).complete)solutions.push(ids);}
 const search=new Filtered(m),root=JSON.stringify(search.semanticState());
 for(let step=0;step<2000;step++){
  assert.equal(canon(search.graph),canon(independentResidualDomains(search,m)));states++;
  for(const solution of solutions)if([...search.placed.keys()].every(id=>solution.includes(id)))
   for(const id of solution)if(!search.placed.has(id))assert(!search.capacityBlocked.has(id),'Pruned a possible completion');
  const d=search.advance();if(['complete','exhausted'].includes(d.kind)){assert.equal(d.kind==='complete',solutions.length>0);break;}
 }
 search.undo(0);assert.equal(JSON.stringify(search.semanticState()),root);
}
// Mark-only dependency can invalidate a candidate far from the changed t-point.
const marked={capacity:2,required:['a','b'],candidates:[
 {id:'a0',t:[{point:'a',value:2}],m:[{point:'outside',lo:0,hi:0}]},
 {id:'a1',t:[{point:'a',value:2}],m:[{point:'outside',lo:1,hi:1}]},
 {id:'b0',t:[{point:'b',value:2}],m:[{point:'outside',lo:0,hi:0}]}]};
const s=new Filtered(marked),before=JSON.stringify(s.semanticState());s.apply('a1');assert.equal(s.decision().kind,'dead');s.undo(0);assert.equal(JSON.stringify(s.semanticState()),before);assert(states>50);
console.log(JSON.stringify({randomModels:50,checkedStates:states,completionPreservation:true,rootRollback:true,markOnlyDependency:true}));
