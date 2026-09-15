import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {portableCloudClass} from './portable-cloud-filter.mjs';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
import {dynamicHalfSupportClass} from './dynamic-half-support.mjs';
const {PointSearch}=await import(pathToFileURL(process.argv[2]));
let seed=9137,subsets=0,states=0;
const rand=n=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed%n;};
const field=x=>({vectors:[[x,0,0]],colors:[[0]]});
function connect(model){
 model.supportGroups=model.required.map(p=>({point:'m'+p,atoms:[p]}));
 model.complementSupport=model.candidates.map(c=>({id:c.id,groups:c.cloudM.map(m=>({point:m.point,partners:model.candidates.filter(d=>d.id!==c.id&&d.base!==c.base&&d.cloudM.some(n=>n.point===m.point&&Math.abs(n.cloud.vectors[0][0]-m.cloud.vectors[0][0])<=2*model.cloudRadius+1e-8)).map(d=>d.id)}))}));
 return model;
}
function valid(model,chosen,complete=false){
 const totals=new Map(model.required.map(p=>[p,0])),base=new Set(),marks=new Map();
 for(const c of chosen){if(base.has(c.base))return false;base.add(c.base);for(const t of c.t)totals.set(t.point,totals.get(t.point)+1);for(const m of c.cloudM){if(!marks.has(m.point))marks.set(m.point,[]);marks.get(m.point).push(m.cloud.vectors[0][0]);}}
 return [...totals.values()].every(v=>complete?v===2:v<=2)&&[...marks.values()].every(v=>Math.max(...v)-Math.min(...v)<=2*model.cloudRadius+2e-10);
}
function audit(e,model){
 const chosen=model.candidates.filter(c=>e.placed.has(c.id)),live=new Set(model.candidates.filter(c=>!e.placed.has(c.id)&&valid(model,[...chosen,c])).map(c=>c.id));
 let changed=true;while(changed){changed=false;for(const id of [...live]){const c=model.candidates.find(c=>c.id===id);for(const g of model.supportGroups){if(!c.t.some(t=>g.atoms.includes(t.point))||e.points.get(g.atoms[0]).total!==0)continue;
  if(!model.candidates.some(d=>live.has(d.id)&&d.id!==id&&d.base!==c.base&&d.cloudM.some(m=>m.point===g.point&&Math.abs(m.cloud.vectors[0][0]-c.cloudM.find(v=>v.point===g.point).cloud.vectors[0][0])<=2*model.cloudRadius+1e-8))){live.delete(id);changed=true;break;}
 }}}
 for(const p of model.required){const expected=e.points.get(p).total<2?[...live].filter(id=>model.candidates.find(c=>c.id===id).t.some(t=>t.point===p)).sort():[];assert.deepEqual([...(e.graph.get(p)?.keys()||[])].sort(),expected);}
 for(const c of model.candidates)assert.deepEqual([...e.reverse.get(c.id)].sort(),live.has(c.id)?c.t.filter(t=>e.points.get(t.point).total<2).map(t=>t.point).sort():[]);
 e.auditGraph();states++;
}
for(let trial=0;trial<100;trial++){
 const n=2+rand(4),count=2+rand(9),model=connect({capacity:2,cloudRadius:.15,required:Array.from({length:n},(_,i)=>String(i)),candidates:Array.from({length:count},(_,i)=>{
  const a=rand(n);let b=rand(n-1);if(b>=a)b++;
  return {id:String(i),base:String(rand(count)),t:[a,b].map(p=>({point:String(p),value:1})),m:[],cloudM:[a,b].map(p=>({point:'m'+p,cloud:field(rand(3)*.2)}))};
 })});
 let solutions=0;for(let bits=0;bits<1<<count;bits++){subsets++;if(valid(model,model.candidates.filter((_,i)=>bits&(1<<i)),true))solutions++;}
 const Engine=dynamicHalfSupportClass(portableCloudClass(linearFrontierClass(PointSearch),model),model),e=new Engine(model),root=JSON.stringify(e.semanticState());
 let last,steps=0;do{audit(e,model);last=e.advance();assert(++steps<10000);}while(!['complete','exhausted','unknown'].includes(last.kind));
 assert.notEqual(last.kind,'unknown');assert.equal(last.kind==='complete',solutions>0);audit(e,model);e.undo(0);audit(e,model);assert.equal(JSON.stringify(e.semanticState()),root);
}
// Composition regression: the linear scheduler must not bypass the portable
// common-value completion gate. This guarded feasible pair is proposer-unknown.
const guarded=connect({capacity:2,cloudRadius:.1,required:['0'],candidates:[0,.20000000015].map((x,i)=>({id:String(i),base:String(i),t:[{point:'0',value:1}],m:[],cloudM:[{point:'m0',cloud:field(x)}]}))});
const Guarded=dynamicHalfSupportClass(portableCloudClass(linearFrontierClass(PointSearch),guarded),guarded),e=new Guarded(guarded);
e.apply('0');e.apply('1');assert.equal(e.decision().kind,'unknown');assert.equal(e.placed.size,2);
console.log(JSON.stringify({models:100,subsets,states,fullSolutionExistence:true,graphAndRollback:true,completionGateComposition:true}));
