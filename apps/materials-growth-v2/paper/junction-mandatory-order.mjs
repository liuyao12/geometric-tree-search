// Declared generation-tie ordering policy. Required connections are inferred
// from the current learned junction domains, never from the training answer.
// They remain ordinary branch choices, not relabeled degree-one forced moves.
export function mandatoryFrontierClass(Base){
 return class MandatoryFrontierSearch extends Base{
  decision(){
   const base=super.decision();if(base.kind!=='branch'||!this.junctionMandatory?.size)return base;
   const generation=this.points.get(base.point).generation;let best=null;
   for(const [point,domain] of this.graph){
    if(this.points.get(point).generation!==generation||![...domain.keys()].some(id=>this.junctionMandatory.has(id)))continue;
    if(!best||domain.size<best.domain.size||(domain.size===best.domain.size&&point.localeCompare(best.point)<0))best={point,domain};
   }
   if(!best)return base;
   const ids=[...best.domain.keys()].sort((a,b)=>Number(this.junctionMandatory.has(b))-Number(this.junctionMandatory.has(a))||
    this.preference(this.candidates.get(b))-this.preference(this.candidates.get(a))||a.localeCompare(b));
   return {kind:'branch',point:best.point,ids,provisional:!this.points.get(best.point).complete,mandatoryPreferred:true};
  }
 };
}
