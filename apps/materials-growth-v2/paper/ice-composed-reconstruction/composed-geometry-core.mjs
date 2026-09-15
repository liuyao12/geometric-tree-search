// Producer for an ordered, finite-pool proof DAG. Independent validation is
// performed by verified-geometry-cores and the standalone Python checker.
export function deriveGeometryCore(model,selectedOwners,point,prior){
 const geometry=new Map(model.candidates.map(c=>[c.base,c.t]));
 const obstruction=owners=>{
  const used=new Set(owners),totals=new Map();for(const g of used)for(const t of geometry.get(g))totals.set(t.point,(totals.get(t.point)||0)+t.value);
  if((totals.get(point)||0)>=model.capacity||prior.some(k=>k.owners.every(g=>used.has(g))))return null;
  const blockers=[];
  for(const [g,t] of geometry)if(t.some(x=>x.point===point)){
   if(used.has(g)){blockers.push({inventory:g,reason:'consumed'});continue;}
   const over=t.find(x=>(totals.get(x.point)||0)+x.value>model.capacity);
   if(over){blockers.push({inventory:g,reason:'capacity',point:over.point});continue;}
   const dependency=prior.findIndex(k=>k.owners.every(owner=>owner===g||used.has(owner)));
   if(dependency<0)return null;blockers.push({inventory:g,reason:'prior-core',dependency});
  }
  return blockers;
 };
 let owners=[...selectedOwners].sort();if(!obstruction(owners))return null;
 for(const g of [...owners]){const smaller=owners.filter(x=>x!==g);if(obstruction(smaller))owners=smaller;}
 if(!owners.length)return null; // Empty contradiction requires separate model-unsat reporting.
 const blockers=obstruction(owners);return {owners,point,blockers,dependencies:[...new Set(blockers.filter(b=>b.reason==='prior-core').map(b=>b.dependency))]};
}
