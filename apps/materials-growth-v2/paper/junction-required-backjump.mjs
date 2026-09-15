// Proof-scoped parent pruning, not an additional learned rule. If a chosen
// candidate was required in its parent, exhaustion of that child exhausts the
// parent too. Verify the requirement independently at the restored parent.
import assert from 'node:assert/strict';
import {independentJunctionDomains} from './junction-marking-arc-filter.mjs';
export function requiredBackjumpClass(Base,model,nodes){
 assert(!model.expand&&model.complete!==false&&model.required.every(p=>typeof p==='string'));
 return class RequiredBackjumpSearch extends Base{
  advance(){
   if(this.status==='exhausted')return {kind:'exhausted'};
   const decision=this.decision();
   if(decision.kind==='dead'){
    while(this.stack.length){
     const frame=this.stack.pop();this.undo(frame.checkpoint);this.stats.backtracks++;
     if(frame.requiredAtParent){
      assert(this.junctionMandatory.has(frame.id));
      const hypothetical={placed:this.placed,branchBlocked:new Set([...(this.branchBlocked||[]),frame.id])};
      const graph=independentJunctionDomains(hypothetical,model,nodes);
      assert([...graph.values()].some(cs=>cs.size===0),'Required-parent pruning lacks independent contradiction');
      this.requiredParentPrunes=(this.requiredParentPrunes||0)+1;continue;
     }
     this.exclude(frame.id);this.status='searching';return {kind:'excluded',id:frame.id,point:frame.point};
    }
    this.undo(0);this.status='exhausted';return {kind:'exhausted',reason:'declared junction model with verified required-parent pruning'};
   }
   const required=decision.kind==='branch'&&decision.mandatoryPreferred;
   const result=super.advance();
   if(required){const frame=this.stack.at(-1);assert.equal(frame.id,result.id);frame.requiredAtParent=true;}
   return result;
  }
 };
}
