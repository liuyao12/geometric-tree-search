import {add,sub,allowedTranslation,placementKey} from '../../apps/3d-lattice-tiler/corona-graph.js';
import {pairCompatible} from '../../apps/3d-lattice-tiler/marking-learning.js';
const key=pair=>pair.map(placementKey).join('|');
// Exhaust ALL capacity-legal relative placements whose assigned m-supports
// overlap, not just the t-contact pairs originally used for classification.
export function auditMarkingContacts(model,fields,labels,transforms){
 const expanded=new Map();
 for(const row of labels)for(const g of transforms)for(const swap of [false,true]){
  const pair=row.pair.map(p=>({oi:g.map[p.oi].oi,translation:add(g.transform(p.translation),g.map[p.oi].shift)}));if(swap)pair.reverse();
  const origin=pair[0].translation,normal=pair.map(p=>({...p,translation:sub(p.translation,origin)}));
  if(normal.some(p=>!allowedTranslation(model,p.translation)))throw Error('Label transport leaves lattice');
  const k=key(normal);if(expanded.has(k)&&expanded.get(k)!==row.status)throw Error('Conflicting transported labels');expanded.set(k,row.status);
 }
 const seen=new Set(),counts={touchCompatible:0,touchConflict:0,noncontactCompatible:0,noncontactConflict:0,rejectedWithoutNegativeLabel:0};
 for(let root=0;root<model.orientations.length;root++)for(let oi=0;oi<model.orientations.length;oi++)for(const a of fields[root])for(const b of fields[oi]){
  if((a.component??0)!==(b.component??0))continue;
  const translation=sub(a.pos,b.pos),pair=[{oi:root,translation:[0,0,0]},{oi,translation}],k=key(pair);
  if(seen.has(k)||!allowedTranslation(model,translation)||root===oi&&translation.every(x=>x===0))continue;seen.add(k);
  const support=new Map(model.orientations[root].cells.map(c=>[c.pos.join(),c.weight]));
  if(model.orientations[oi].cells.some(c=>(support.get(add(c.pos,translation).join())??0)+c.weight>model.capacity))continue;
  const touching=model.orientations[oi].cells.some(c=>support.has(add(c.pos,translation).join())),compatible=pairCompatible(fields,pair);
  counts[`${touching?'touch':'noncontact'}${compatible?'Compatible':'Conflict'}`]++;
  if(!compatible&&expanded.get(k)!=='invalid')counts.rejectedWithoutNegativeLabel++;
 }
 return {expandedLabels:expanded.size,counts,noExtraPairExclusions:counts.noncontactConflict===0&&counts.rejectedWithoutNegativeLabel===0,scope:'Exhaustive pair-exclusion audit in the declared lattice and orientation group. Preservation of infinite tilings additionally relies on the negative local labels; no standalone UNSAT proof is supplied.'};
}
