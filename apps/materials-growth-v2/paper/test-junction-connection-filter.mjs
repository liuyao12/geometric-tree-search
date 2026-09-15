import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {connectionMarkingClass,independentConnectionDomains} from './junction-connection-filter.mjs';
import {branchExclusionClass} from './branch-local-exclusions.mjs';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
import {mandatoryFrontierClass} from './junction-mandatory-order.mjs';
const {PointSearch}=await import(pathToFileURL(process.argv[2]));
let seed=143,subsets=0,states=0,restrictedSolutions=0;
const rand=n=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return (seed>>>7)%n;};
const canon=g=>JSON.stringify([...g].map(([p,cs])=>[p,[...cs].sort()]).sort());
for(let trial=0;trial<150;trial++){
 const model={capacity:2,required:['a','b','c'],candidates:Array.from({length:7},(_,i)=>({id:String(i),
  t:['a','b','c'].filter(()=>rand(3)).slice(0,2).map(point=>({point,value:1+rand(2)})),
  m:rand(2)?[]:[{point:'outside',channel:'0',lo:i%2,hi:i%2}]})).filter(c=>c.t.length)};
 const solutions=[];
 for(let mask=0;mask<2**model.candidates.length;mask++){
  subsets++;const selected=model.candidates.filter((_,i)=>mask&(1<<i)),totals=new Map(model.required.map(p=>[p,0])),marks=new Set();
  for(const c of selected){for(const x of c.t)totals.set(x.point,totals.get(x.point)+x.value);for(const x of c.m)marks.add(x.lo);}
  if([...totals.values()].every(v=>v===2)&&marks.size<=1)solutions.push(selected.map(c=>c.id));
 }
 const training=solutions.filter(()=>rand(2));
 const nodes=model.required.filter(()=>rand(2)).map(point=>{
  const incident=model.candidates.filter(c=>c.t.some(x=>x.point===point)).map(c=>c.id);
  const unique=new Map(training.map(s=>{const local=s.filter(id=>incident.includes(id));return [JSON.stringify(local),local];}));
  return {point,incident,states:[...unique.values()]};
 });
 const edges=model.candidates.flatMap(c=>{
  const touched=nodes.filter(n=>n.incident.includes(c.id));if(touched.length!==2)return [];
  const pairs=new Map();for(const selected of training)if(selected.includes(c.id)){
   const pair=touched.map(n=>n.states.findIndex(s=>JSON.stringify(s)===JSON.stringify(selected.filter(id=>n.incident.includes(id)))));pairs.set(JSON.stringify(pair),pair);
  }return [{candidate:c.id,points:touched.map(n=>n.point),allowedPresentStates:[...pairs.values()]}];
 });
 const allowed=solutions.filter(s=>{
  const labels=new Map(nodes.map(n=>[n.point,n.states.findIndex(t=>JSON.stringify(t)===JSON.stringify(s.filter(id=>n.incident.includes(id))))]));
  return [...labels.values()].every(x=>x>=0)&&edges.every(edge=>!s.includes(edge.candidate)||edge.allowedPresentStates.some(pair=>JSON.stringify(pair)===JSON.stringify(edge.points.map(p=>labels.get(p)))));
 });restrictedSolutions+=allowed.length;
 const Engine=mandatoryFrontierClass(linearFrontierClass(branchExclusionClass(connectionMarkingClass(PointSearch,nodes,edges,model)))),e=new Engine(model),root=JSON.stringify(e.semanticState());let terminal=false;
 const rootMandatory=[...e.junctionMandatory].sort();
 for(let step=0;step<10000;step++){
  states++;assert.equal(canon(e.graph),canon(independentConnectionDomains(e,model,nodes,edges).graph));e.auditGraph();
  const decision=e.decision(),rows=[...e.graph].map(([p,c])=>({n:c.size,g:e.points.get(p).generation}));
  if(rows.some(x=>x.n===0))assert.equal(decision.kind,'dead');
  else if(rows.some(x=>x.n===1))assert.equal(decision.kind,'forced');
  else if(rows.length){assert.equal(decision.kind,'branch');assert.equal(e.points.get(decision.point).generation,Math.min(...rows.map(x=>x.g)));}
  const result=e.advance();
  if(['complete','exhausted'].includes(result.kind)){assert.equal(result.kind==='complete',allowed.length>0);terminal=true;break;}
 }
 assert(terminal);e.undo(0);assert.equal(JSON.stringify(e.semanticState()),root);assert.deepEqual([...e.junctionMandatory].sort(),rootMandatory);
}
const Probe=mandatoryFrontierClass(linearFrontierClass(PointSearch)),probe=new Probe({capacity:2,required:['early','late'],candidates:[
 {id:'e0',t:[{point:'early',value:1}]},{id:'e1',t:[{point:'early',value:1}]},
 {id:'l0',t:[{point:'late',value:1}]},{id:'l1',t:[{point:'late',value:1}]}]});
probe.points.get('late').generation=1;probe.junctionMandatory=new Set(['l0']);assert.equal(probe.decision().point,'early');
probe.points.get('late').generation=0;assert.equal(probe.decision().point,'late');assert.equal(probe.decision().ids[0],'l0');
// Handcrafted decision graph controls, not engine-transition tests.
probe.graph.get('early').delete('e1');assert.equal(probe.decision().kind,'forced');assert.equal(probe.decision().point,'early');
probe.graph.get('late').clear();assert.equal(probe.decision().kind,'dead');
console.log(JSON.stringify({models:150,subsets,states,restrictedSolutions,completionAgreement:true,graphAgreement:true,rootRollback:true,generationAndGlobalPriorityChecks:true}));
// Exercise the BigInt fallback: 35 distinct three-of-seven states per node.
const big={capacity:3,required:['x','y'],candidates:[{id:'shared',t:[{point:'x',value:1},{point:'y',value:1}],m:[]}]};
for(const p of big.required)for(let i=0;i<6;i++)big.candidates.push({id:`${p}${i}`,t:[{point:p,value:1}],m:[]});
const bn=big.required.map(point=>{
 const incident=big.candidates.filter(c=>c.t.some(t=>t.point===point)).map(c=>c.id),local=[];
 for(let a=0;a<7;a++)for(let b=a+1;b<7;b++)for(let c=b+1;c<7;c++)local.push([incident[a],incident[b],incident[c]]);
 return {point,incident,states:local};
});
const pairs=[];bn[0].states.forEach((s,i)=>{if(s.includes('shared'))bn[1].states.forEach((t,j)=>{if(t.includes('shared'))pairs.push([i,j]);});});
const be=[{candidate:'shared',points:['x','y'],allowedPresentStates:pairs}],Big=mandatoryFrontierClass(linearFrontierClass(branchExclusionClass(connectionMarkingClass(PointSearch,bn,be,big)))),large=new Big(big);
const bigRoot=JSON.stringify(large.semanticState());assert.equal(typeof large.connectionDomains[0],'bigint');let last;
for(let step=0;step<50;step++){assert.equal(canon(large.graph),canon(independentConnectionDomains(large,big,bn,be).graph));last=large.advance();if(['complete','exhausted'].includes(last.kind))break;}
assert.equal(last.kind,'complete');large.undo(0);assert.equal(JSON.stringify(large.semanticState()),bigRoot);
console.log(JSON.stringify({bigIntStateCount:35,bigIntArcAndRollback:true}));
