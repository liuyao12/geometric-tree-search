// Display-only projection of the oracle frames. Never decorates an unmarked
// corona witness with provisional constraints, and never supplies search data.
export function learningSearchView(model,event,previous=null){
 const placements=event.placements??previous?.placements??[],pair=event.pair??previous?.pair??placements.slice(0,2);
 const required=new Map();
 for(const p of pair)for(const c of model.orientations[p.oi].cells){const pos=c.pos.map((x,i)=>x+p.translation[i]);required.set(pos.join(),{pos});}
 const nodes=event.phase==='pair'?0:event.nodes??previous?.nodes??0,backtracks=event.phase==='pair'?0:event.backtracks??previous?.backtracks??0;
 const status=event.status??(event.action==='dead'?'dead end':event.action??event.phase??'searching');
 const outcome=event.type==='marking-learned'?(event.marking.accepted?'Marking validated':'Marking not activated'):status;
 return {model:{...model,orientations:model.orientations.map(o=>({...o,marks:[]})),required:[...required.values()]},placements,pair,
  deadPoint:event.action==='dead'?event.point:null,
  title:`Collecting samples · ${outcome}`,
  detail:`${placements.length} tiles · ${event.totalPairs??previous?.totalPairs??0} pairs · ${nodes} attempts · ${backtracks} backtracks`,
  totalPairs:event.totalPairs??previous?.totalPairs??0,nodes,backtracks};
}
