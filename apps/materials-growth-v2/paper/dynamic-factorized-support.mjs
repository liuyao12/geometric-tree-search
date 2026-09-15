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
  // Completeness is an external precondition, checked by the independent
  // index verifier and hash-bound by the material runner. Validate shape here.
  this.partnerIndex=options.partnerIndex??null;
  if(this.partnerIndex){
   const g=this.partnerIndex;this.endpointIndex=this.blocks.map(b=>b.endpointChoices.map(cs=>new Array(cs.length)));
   let n=0;
   for(const b of this.blocks)for(let side=0;side<2;side++)for(let j=0;j<b.endpointChoices[side].length;j++){
    if(JSON.stringify(g.records[n])!==JSON.stringify([b.index,side,j]))throw Error('Partner-index records mismatch');
    this.endpointIndex[b.index][side][j]=n++;
   }
   if(g.records.length!==n||g.neighbors.length!==n)throw Error('Partner-index size mismatch');
   for(const ns of g.neighbors){let previous=-1;for(const k of ns){if(!Number.isSafeInteger(k)||k<=previous||k>=n)throw Error('Invalid partner-index adjacency');previous=k;}}
  }
  this.supportStats={refreshes:0,passes:0,pairChecks:0,removed:0};
  this.refresh(new Set(this.points.keys()));
 }
 *partners(index,side,j,info){
  if(this.partnerIndex){for(const k of this.partnerIndex.neighbors[this.endpointIndex[index][side][j]])yield this.partnerIndex.records[k];}
  else for(const m of info.members)for(const k of this.blocks[m.index].domain.endpointIndices(m.side))yield [m.index,m.side,k];
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
      for(const [otherIndex,otherSide,k] of this.partners(index,side,j,info)){
       const other=this.blocks[otherIndex];
       if(other.inventory===b.inventory||other.domain.count===0n||!other.domain.containsEndpoint(otherSide,k))continue;
       if(other.markPoints[otherSide]!==point)throw Error('Partner-index anchor mismatch');
        this.supportStats.pairChecks++;
        if(this.compatible(value,[{value:other.endpointChoices[otherSide][k]}])){supported=true;break;}
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
