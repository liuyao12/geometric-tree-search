// Necessary complementary support, rebuilt to a fixed point after every state
// change. Correctness-first integration: not yet an incremental performance claim.
import {FactorizedPointSearch} from './factorized-point-search.mjs';
export class DynamicFactorizedSupportSearch extends FactorizedPointSearch {
 constructor(model,options={}){
  super(model,options);
  if(model.capacity!==2||model.required.some(p=>typeof p!=='string')||this.blocks.some(b=>b.t.some(t=>t.value!==1)))throw Error('Requires finite complete half-weight point model');
  this.supportAnchors=new Map();
  for(const b of this.blocks)for(const [side,point] of b.markPoints.entries()){
   if(!this.supportAnchors.has(point))this.supportAnchors.set(point,{members:[]});
   this.supportAnchors.get(point).members.push({index:b.index,side});
  }
  for(const [point,info] of this.supportAnchors){
   const indices=new Set(info.members.map(m=>m.index));
   info.witness=model.required.find(p=>this.blocks.every(b=>b.t.some(t=>t.point===p)===indices.has(b.index)));
   if(info.witness===undefined)throw Error(`No required incidence witness for ${point}`);
  }
  this.supportStats={refreshes:0,passes:0,pairChecks:0,removed:0};
  this.refresh(new Set(this.points.keys()));
 }
 refresh(changed,inventories=new Set()){
  if(!this.supportAnchors)return super.refresh(changed,inventories);
  // Undo must first revive everything allowed by the restored base state.
  // No removal proved in a child is retained in its parent.
  super.refresh(new Set(this.points.keys()),new Set(this.inventoryDependencies.keys()));
  this.supportStats.refreshes++;let changedSupport;
  do{
   changedSupport=false;this.supportStats.passes++;
   for(const [point,info] of this.supportAnchors){
    const total=this.points.get(info.witness).total;
    // A selected half already supplies the complement when total==1. Base
    // legality checks its actual m-value. At total==2 no incident block is legal.
    if(total!==0)continue;
    for(const {index,side} of info.members){
     const b=this.blocks[index];if(b.domain.count===0n)continue;
     const before=[...b.domain.endpointIndices(side)],keep=[];
     for(const j of before){
      const value=b.endpointChoices[side][j];let supported=false;
      for(const member of info.members){
       const other=this.blocks[member.index];
       if(other.inventory===b.inventory||other.domain.count===0n)continue;
       for(const k of other.domain.endpointIndices(member.side)){
        this.supportStats.pairChecks++;
        if(this.compatible(value,[{value:other.endpointChoices[member.side][k]}])){supported=true;break;}
       }
       if(supported)break;
      }
      if(supported)keep.push(j);
     }
     if(keep.length!==before.length){b.domain.setAllowed(side,keep);changedSupport=true;this.supportStats.removed+=before.length-keep.length;}
    }
   }
  }while(changedSupport);
  for(const b of this.blocks){
   b.domain.trail=[];
   for(const t of b.t){const at=this.graph.get(t.point);if(at){if(b.domain.count>0n)at.add(b.index);else at.delete(b.index);}}
  }
 }
}
