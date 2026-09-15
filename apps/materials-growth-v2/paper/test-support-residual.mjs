// Exhaustive composition check: immutable certified exclusions + residual filter
// + parent-local exclusions + the reference decision order.
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {certifiedZeroSupport} from './certified-zero-support.mjs';
import {residualCapacityClass,independentResidualDomains} from './residual-capacity-filter.mjs';
import {branchExclusionClass} from './branch-local-exclusions.mjs';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
const {PointSearch}=await import(pathToFileURL(process.argv[2]));
let rng=7341,states=0,subsets=0;
const rand=n=>{rng=(Math.imul(rng,1664525)+1013904223)>>>0;return rng%n;};
const canonical=g=>JSON.stringify([...g].map(([p,cs])=>[p,[...cs].sort()]).sort());
for(let trial=0;trial<100;trial++){
 const model={capacity:4,required:['0','1','2','3'],candidates:[
  {id:'000000',t:[{point:'0',value:4},{point:'1',value:3}],m:[]},
  {id:'000001',t:[{point:'0',value:4},{point:'1',value:4}],m:[]},
  ...Array.from({length:7},(_,i)=>({id:String(i+2).padStart(6,'0'),
   t:['2','3'].filter(()=>rand(3)).map(point=>({point,value:1+rand(4)})),
   m:rand(3)?[{point:'outside',channel:'0',lo:0,hi:0}]:[{point:'outside',channel:'0',lo:1,hi:1}]})).filter(c=>c.t.length)]};
 const solutions=[];
 for(let mask=0;mask<2**model.candidates.length;mask++){
  subsets++;const chosen=model.candidates.filter((_,i)=>mask&(1<<i)),totals=new Map(model.required.map(p=>[p,0])),marks=new Map();let legal=true;
  for(const c of chosen){for(const x of c.t)totals.set(x.point,totals.get(x.point)+x.value);
   for(const x of c.m){if(marks.has(x.point)&&marks.get(x.point)!==x.lo)legal=false;marks.set(x.point,x.lo);}}
  if(legal&&[...totals.values()].every(x=>x===4))solutions.push(new Set(chosen.map(c=>c.id)));
 }
 const excluded=certifiedZeroSupport(model,{excluded:[0],y:[[0,'1'],[1,'-1']],z:[],bound:'0'});
 for(const solution of solutions)assert(!solution.has('000000'));
 class Support extends PointSearch{reason(c){return super.reason(c)||(excluded.has(c.id)?'certified-zero-support':null);}}
 const Engine=linearFrontierClass(branchExclusionClass(residualCapacityClass(Support)));
 const e=new Engine(model);e.staticCertifiedExclusions=excluded;const root=JSON.stringify(e.semanticState());let terminal=false;
 for(let step=0;step<10000;step++){
  states++;assert.equal(canonical(e.graph),canonical(independentResidualDomains(e,model)));e.auditGraph();
  const d=e.decision(),rows=[...e.graph].map(([p,cs])=>({size:cs.size,g:e.points.get(p).generation}));
  if(rows.some(x=>x.size===0))assert.equal(d.kind,'dead');
  else if(rows.some(x=>x.size===1))assert.equal(d.kind,'forced');
  else if(rows.length){assert.equal(d.kind,'branch');assert.equal(e.points.get(d.point).generation,Math.min(...rows.map(x=>x.g)));}
  const result=e.advance();
  if(['complete','exhausted'].includes(result.kind)){assert.equal(result.kind==='complete',solutions.length>0);terminal=true;break;}
 }
 assert(terminal);e.undo(0);assert.equal(JSON.stringify(e.semanticState()),root);
}
console.log(JSON.stringify({models:100,subsets,states,completionAgreement:true,graphAgreement:true,rootRollback:true}));
