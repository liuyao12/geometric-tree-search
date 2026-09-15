// Point-state/dependency integration for exact factorized candidate domains.
// This is not yet the DFS driver. Endpoint legality must be separable by marking
// point; terminal common-value verification remains the adapter's obligation.
import {FactorizedCandidateDomain,factorizedDecision} from './factorized-candidate-domain.mjs';
export class FactorizedPointState {
 constructor(model,{compatible=(value,active)=>active.every(a=>a.value===value)}={}){
  if(!Number.isSafeInteger(model.capacity)||model.capacity<1)throw Error('Invalid capacity');
  this.capacity=model.capacity;this.compatible=compatible;this.points=new Map();this.graph=new Map();this.dependencies=new Map();this.inventoryDependencies=new Map();this.owners=new Map();this.placed=new Map();this.trail=[];
  for(const item of model.required){const p=typeof item==='string'?{id:item}:item;this.ensure(p.id,{active:true,root:0,complete:p.complete??true});}
  const ids=new Set();
  this.blocks=model.blocks.map((input,index)=>{
   if(typeof input.id!=='string'||typeof input.inventory!=='string'||ids.has(input.id))throw Error('Invalid block/inventory');ids.add(input.id);
   if(input.markPoints.length!==2||new Set(input.markPoints).size!==2||input.endpointChoices.length!==2)throw Error('Two distinct marking points required');
   if(!input.t.length||new Set(input.t.map(t=>t.point)).size!==input.t.length||input.t.some(t=>!Number.isSafeInteger(t.value)||t.value<=0||t.value>this.capacity))throw Error('Invalid positive t support');
   const block={...input,index,domain:new FactorizedCandidateDomain(...input.endpointChoices.map(a=>a.length))};
   for(const id of new Set([...input.t.map(t=>t.point),...input.markPoints])){
    this.ensure(id);if(!this.dependencies.has(id))this.dependencies.set(id,new Set());this.dependencies.get(id).add(index);
   }
   if(!this.inventoryDependencies.has(input.inventory))this.inventoryDependencies.set(input.inventory,new Set());this.inventoryDependencies.get(input.inventory).add(index);
   // Mirror initial explicit-candidate insertion before the final root refresh.
   if(block.domain.count>0n)for(const t of input.t){const p=this.points.get(t.point);if(p.active&&!this.graph.has(p.id))this.graph.set(p.id,new Set());}
   return block;
  });
  this.refresh(new Set(this.points.keys()));
 }
 ensure(id,{active=false,root=Infinity,complete=true}={}){
  if(!this.points.has(id))this.points.set(id,{id,active,root,generation:root,complete,total:0,marks:[]});return this.points.get(id);
 }
 candidateId(index,left,right){return [index,left,right].map(n=>String(n).padStart(16,'0')).join('/');}
 decode(id){
  const parts=id.split('/');if(parts.length!==3)throw Error('Invalid candidate id');const [index,left,right]=parts.map(Number);
  const block=this.blocks[index];if(!block||this.candidateId(index,left,right)!==id)throw Error('Invalid candidate id');
  block.domain.validate(0,left);block.domain.validate(1,right);return {index,left,right,block};
 }
 refresh(changed,inventories=new Set()){
  const affected=new Set();
  for(const id of changed){
   const p=this.points.get(id);
   if(p.active&&p.total<this.capacity){if(!this.graph.has(id))this.graph.set(id,new Set());}else this.graph.delete(id);
   for(const index of this.dependencies.get(id)||[])affected.add(index);
  }
  for(const inventory of inventories)for(const index of this.inventoryDependencies.get(inventory)||[])affected.add(index);
  for(const index of affected){
   const b=this.blocks[index],domain=b.domain;
   domain.setEnabled(!this.owners.has(b.inventory)&&b.t.every(t=>this.points.get(t.point).total+t.value<=this.capacity));
   for(let side=0;side<2;side++){
    const active=this.points.get(b.markPoints[side]).marks;
    domain.setAllowed(side,active.length?b.endpointChoices[side].map((value,i)=>this.compatible(value,active)?i:null).filter(i=>i!==null):null);
   }
   domain.trail=[]; // Derived state: point/inventory rollback revalidates it.
   for(const t of b.t){
    const at=this.graph.get(t.point);if(!at)continue;
    if(domain.count>0n)at.add(index);else at.delete(index);
   }
  }
 }
 frontier(){return [...this.graph].map(([id,indices])=>({...this.points.get(id),blocks:[...indices].map(i=>this.blocks[i].domain)}));}
 decision(){return factorizedDecision(this.frontier());}
 *candidateIds(point){
  for(const i of [...(this.graph.get(point)||[])].sort((a,b)=>a-b))for(const [left,right] of this.blocks[i].domain.values())yield this.candidateId(i,left,right);
 }
 degree(point){return [...(this.graph.get(point)||[])].reduce((n,i)=>n+this.blocks[i].domain.count,0n);}
 checkpoint(){return this.trail.length;}
 apply(id,seed=false){
  const {index,left,right,block:b}=this.decode(id);
  if(!b.domain.has(left,right))throw Error('Illegal placement');
  const touched=new Set([...b.t.map(t=>t.point),...b.markPoints]);
  const before=[...touched].map(p=>[p,{...this.points.get(p),marks:[...this.points.get(p).marks]}]);
  const checkpoint=this.checkpoint(),existing=b.t.map(t=>this.points.get(t.point).generation).filter(Number.isFinite);
  const generation=seed?0:existing.length?Math.min(...existing)+1:0;
  const undoPoints=new Set([...b.markPoints].reverse().concat(b.t.map(t=>t.point).reverse(),[...touched]));
  this.trail.push({id,inventory:b.inventory,before,undoPoints});this.owners.set(b.inventory,id);this.placed.set(id,{generation,index,left,right});
  for(const t of b.t){const p=this.points.get(t.point);p.total+=t.value;p.generation=Math.min(p.generation,generation);p.active=true;}
  for(const [side,choice] of [left,right].entries())this.points.get(b.markPoints[side]).marks.push({value:b.endpointChoices[side][choice],owner:id});
  try{this.refresh(touched,new Set([b.inventory]));}catch(error){this.undo(checkpoint);throw error;}
  return checkpoint;
 }
 undo(checkpoint){
  if(!Number.isInteger(checkpoint)||checkpoint<0||checkpoint>this.trail.length)throw Error('Invalid checkpoint');
  const touched=new Set(),inventories=new Set();
  while(this.trail.length>checkpoint){const r=this.trail.pop();this.placed.delete(r.id);this.owners.delete(r.inventory);inventories.add(r.inventory);for(const id of r.undoPoints)touched.add(id);for(const [id,old] of r.before)Object.assign(this.points.get(id),old);}
  this.refresh(touched,inventories);
 }
}
