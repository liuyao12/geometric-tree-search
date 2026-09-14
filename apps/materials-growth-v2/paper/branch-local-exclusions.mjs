// Search-control variant: a failed candidate is excluded only in its proved
// parent context. Exclusions are on the same undo trail as placements. This
// avoids revisiting failed combinations through different placement orders.
export function branchExclusionClass(Base){
 return class BranchExclusionSearch extends Base{
  reason(c){return super.reason(c)||(this.branchBlocked?.has(c.id)?'failed-parent-choice':null);}
  exclude(id){
   this.branchBlocked??=new Set();if(this.branchBlocked.has(id))return;
   const c=this.candidates.get(id),points=[...new Set([...c.t.map(x=>x.point),...c.m.map(x=>x.point)])];
   this.trail.push(Object.assign(()=>this.branchBlocked.delete(id),{points}));this.branchBlocked.add(id);
   this.exclusionCount=(this.exclusionCount||0)+1;this.refresh(new Set(points));
  }
  advance(){
   if(this.status==='exhausted')return {kind:'exhausted'};
   const d=this.decision();
   if(d.kind==='unknown'){this.status='unknown';return d;}
   if(d.kind==='complete'){this.status='consistent finite patch';return d;}
   if(d.kind==='dead'){
    if(!this.stack.length){this.undo(0);this.status='exhausted';return {kind:'exhausted',reason:'declared candidate model'};}
    const frame=this.stack.pop();this.undo(frame.checkpoint);this.stats.backtracks++;this.exclude(frame.id);
    this.status='searching';return {kind:'excluded',id:frame.id,point:frame.point};
   }
   const id=d.ids[0];
   if(d.kind==='branch'){this.stack.push({checkpoint:this.trail.length,id,point:d.point});this.stats.branches++;}
   else this.stats.forced++;
   this.stats.attempts++;this.apply(id);this.stats.accepted++;this.status='searching';return {...d,id};
  }
  semanticState(){return {...super.semanticState(),parentExclusions:[...(this.branchBlocked||[])].sort()};}
 };
}
