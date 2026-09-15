// Representation-only scheduler optimization. Preserve the base comparator,
// first-insertion dead/unknown choice and candidate preference ordering exactly.
// No pruning, changed point model, geometric heuristic or material information.
export function linearFrontierClass(Base){
 return class LinearFrontierSearch extends Base{
  decision(){
   let forced=null,unknown=null,branch=null;
   const earlier=(a,b)=>!b || a.point.generation-b.point.generation<0 ||
    (a.point.generation===b.point.generation && (a.cs.size<b.cs.size ||
     (a.cs.size===b.cs.size && a.point.id.localeCompare(b.point.id)<0)));
   for(const [id,cs] of this.graph){
    const point=this.points.get(id),row={point,cs};
    if(!cs.size && point.complete)return {kind:'dead',point:id};
    if(cs.size===1 && point.complete && earlier(row,forced))forced=row;
    if(!cs.size && !point.complete && !unknown)unknown=row;
    if(earlier(row,branch))branch=row;
   }
   if(forced)return {kind:'forced',point:forced.point.id,ids:[...forced.cs.keys()]};
   if(unknown)return {kind:'unknown',point:unknown.point.id,reason:'unresolved continuous pose domain'};
   if(!branch)return {kind:'complete'};
   const ids=[...branch.cs.keys()];
   ids.sort((a,b)=>this.preference(this.candidates.get(b))-this.preference(this.candidates.get(a)) || a.localeCompare(b));
   return {kind:'branch',point:branch.point.id,ids,provisional:!branch.point.complete};
  }
 };
}
