// Lazy DFS over the full decorated candidate universe, not geometric projection.
// Branch iterators resume only after exact rollback to their saved parent state.
import {FactorizedPointState} from './factorized-point-state.mjs';
export class FactorizedPointSearch extends FactorizedPointState {
 constructor(model,options={}){
  super(model,options);this.stack=[];this.status='ready';this.terminalCheck=options.terminalCheck??(()=>({valid:true}));
  this.stats={attempts:0,accepted:0,forced:0,branches:0,backtracks:0};
 }
 advance(){
  if(this.status==='exhausted')return {kind:'exhausted'};
  const d=this.decision();
  if(d.kind==='unknown'){this.status='unknown';return d;}
  if(d.kind==='complete'){
   const check=this.terminalCheck(this);
   if(!check.valid){this.status='unknown';return {kind:'unknown',reason:check.reason??'common value not verified'};}
   this.status='consistent finite patch';return d;
  }
  if(d.kind==='dead'){
   while(this.stack.length){
    const frame=this.stack.at(-1);this.undo(frame.checkpoint);this.stats.backtracks++;
    const next=frame.iterator.next();
    if(!next.done){this.stats.attempts++;this.apply(next.value);this.stats.accepted++;this.status='searching';return {kind:'alternative',id:next.value,point:frame.point};}
    this.stack.pop();
   }
   this.undo(0);this.status='exhausted';return {kind:'exhausted',reason:'declared candidate model'};
  }
  const iterator=this.candidateIds(d.point),first=iterator.next();
  if(first.done)throw Error('Nonempty frontier decision has no candidate');
  if(d.kind==='branch'){
   this.stack.push({checkpoint:this.checkpoint(),iterator,point:d.point});this.stats.branches++;
  }else this.stats.forced++;
  this.stats.attempts++;this.apply(first.value);this.stats.accepted++;this.status='searching';
  return {...d,id:first.value};
 }
}
