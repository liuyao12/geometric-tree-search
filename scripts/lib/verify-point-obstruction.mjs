import {allowedTranslation} from '../../apps/3d-lattice-tiler/corona-graph.js';
// Independent t-only replay of a recorded dead point; no SAT variables or
// geometric collision predicate is used to justify the obstruction.
export function verifyPointObstruction(model,{deadPoint,placements}){
 const totals=new Map(),used=new Set();
 for(const p of placements){
  const o=model.orientations[p.oi],id=`${p.oi}@${p.translation}`;
  if(!o||used.has(id)||!allowedTranslation(model,p.translation))throw Error('Invalid obstruction placement');used.add(id);
  for(const c of o.cells){const key=c.pos.map((v,i)=>v+p.translation[i]).join(),n=(totals.get(key)??0)+c.weight;if(n>model.capacity)throw Error('Obstruction exceeds capacity');totals.set(key,n);}
 }
 const n=totals.get(deadPoint.join())??0;if(n<=0||n>=model.capacity)throw Error('Obstruction point is not exposed');
 for(let oi=0;oi<model.orientations.length;oi++)for(const anchor of model.orientations[oi].cells){
  const translation=deadPoint.map((v,i)=>v-anchor.pos[i]);if(!allowedTranslation(model,translation)||used.has(`${oi}@${translation}`))continue;
  if(model.orientations[oi].cells.every(c=>(totals.get(c.pos.map((v,i)=>v+translation[i]).join())??0)+c.weight<=model.capacity))throw Error('Obstruction has a legal candidate');
 }
 return true;
}
