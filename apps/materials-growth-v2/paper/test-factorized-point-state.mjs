import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {FactorizedPointState} from './factorized-point-state.mjs';
import {FactorizedPointSearch} from './factorized-point-search.mjs';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
const {PointSearch}=await import(pathToFileURL(process.argv[2]));
class Explicit extends linearFrontierClass(PointSearch){
 refresh(changed){super.refresh(changed);for(const id of this.candidates.keys())this.updateCandidate(id);}
}
let seed=152873,states=0,membershipChecks=0,rollbacks=0,searchAdvances=0,complete=0,exhausted=0,unknown=0;
const random=n=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed%n;};
const id=(i,a,b)=>[i,a,b].map(n=>String(n).padStart(16,'0')).join('/');
const compatible=(value,active)=>active.every(a=>a.value===value);
for(let trial=0;trial<300;trial++){
 const points=['p0','p1','p2','p3','p4'],marks=['p0','p3','m0','m1'];
 const model={capacity:2,required:[{id:'p0',complete:true},{id:'p1',complete:random(5)!==0}],blocks:[]};
 for(let i=0;i<2+random(4);i++){
  const support=points.filter(()=>random(2));if(!support.length)support.push('p2');
  const markPoints=[marks[random(marks.length)]];markPoints.push(marks.filter(p=>p!==markPoints[0])[random(3)]);
  model.blocks.push({id:`b${i}`,inventory:`v${random(3)}`,t:support.map(point=>({point,value:1+random(2)})),markPoints,
   endpointChoices:Array.from({length:2},()=>Array.from({length:1+random(3)},()=>random(3)))});
 }
 if(trial%3===0){
  for(const q of model.required)q.complete=true;
  for(const point of ['p0','p1'])model.blocks.push({id:`fallback_${point}`,inventory:`fallback_${point}`,t:[{point,value:2}],
   markPoints:[`z${point}L`,`z${point}R`],endpointChoices:[[0,0],[0,0]]});
 }
 const compact=new FactorizedPointSearch(model,{compatible}),candidates=[];
 model.blocks.forEach((b,i)=>b.endpointChoices[0].forEach((a,j)=>b.endpointChoices[1].forEach((value,k)=>candidates.push({
  id:id(i,j,k),inventory:b.inventory,t:b.t,m:[{point:b.markPoints[0],lo:a,hi:a},{point:b.markPoints[1],lo:value,hi:value}],index:i,left:j,right:k
 }))));
 const reference=new Explicit({capacity:2,required:model.required,candidates,
  constraint:(c,e)=>[...e.placed.keys()].some(id=>e.candidates.get(id).inventory===c.inventory)?'inventory':null});
 const audit=()=>{
  assert.deepEqual([...compact.graph.keys()],[...reference.graph.keys()]);
  for(const [point] of compact.graph){
   assert.deepEqual([...compact.candidateIds(point)],[...reference.graph.get(point).keys()].sort((a,b)=>a.localeCompare(b)));
   assert.equal(compact.degree(point),BigInt(reference.graph.get(point).size));
  }
  for(const c of candidates){assert.equal(compact.blocks[c.index].domain.has(c.left,c.right),!reference.reason(reference.candidates.get(c.id)));membershipChecks++;}
  for(const [id,p] of compact.points){
   const q=reference.points.get(id);assert(q);
   for(const key of ['total','generation','active','root','complete'])assert.equal(p[key],q[key],key);
   assert.deepEqual(p.marks.map(a=>[a.owner,a.value]),(q.marks.get('0')||[]).map(a=>[a.owner,a.lo]));
  }
  assert.deepEqual([...compact.placed].map(([id,p])=>[id,p.generation]),[...reference.placed].map(([id,p])=>[id,p.generation]));
  const a=compact.decision(),b=reference.decision();assert.equal(a.kind,b.kind);assert.equal(a.point,b.point);
  if(a.kind==='branch')assert.equal(a.provisional,b.provisional);
  assert.equal(compact.owners.size,compact.placed.size);states++;
 };
 audit();const checkpoints=[];
 for(let step=0;step<50;step++){
  if(checkpoints.length&&random(3)===0){const [a,b]=checkpoints.pop();compact.undo(a);reference.undo(b);rollbacks++;}
  else{
   const legal=candidates.filter(c=>!reference.reason(reference.candidates.get(c.id)));
   if(legal.length){const c=legal[random(legal.length)],seedMove=random(10)===0;checkpoints.push([compact.apply(c.id,seedMove),reference.apply(c.id,seedMove)]);}
  }
  audit();
 }
 compact.undo(0);reference.undo(0);audit();assert.equal(compact.placed.size,0);
 for(let step=0;step<300;step++){
  const actual=compact.advance(),expected=reference.advance();
  assert.equal(actual.kind,expected.kind);assert.equal(actual.id,expected.id);assert.equal(actual.point,expected.point);
  for(const key of ['attempts','accepted','forced','branches','backtracks'])assert.equal(compact.stats[key],reference.stats[key]);
  audit();searchAdvances++;
  if(actual.kind==='complete'){complete++;break;}
  if(actual.kind==='exhausted'){exhausted++;break;}
  if(actual.kind==='unknown'){unknown++;break;}
 }
 compact.undo(0);reference.undo(0);audit();
}
const gate=new FactorizedPointSearch({capacity:1,required:[],blocks:[]},{terminalCheck:()=>({valid:false,reason:'test unknown'})});
assert.equal(gate.advance().kind,'unknown');assert.notEqual(gate.status,'exhausted');
console.log(JSON.stringify({models:300,states,membershipChecks,rollbacks,searchAdvances,complete,exhausted,unknown,referencePointDecisions:true,completeIncidence:true,
 pointTotalsAndGenerations:true,extendedMarkDependencies:true,sharedInventory:true,
 lazyBacktrackingLockstep:true,unknownCompletionNotPruned:true,
 limits:'Lockstep with scalar equality markings. Cloud-set semantics and material execution still require separate tests.'}));
