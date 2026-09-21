// Exact unmarked pair orbits. These helpers do not infer labels from similarity.
import {add,sub,allowedTranslation,placementKey} from '../../apps/3d-lattice-tiler/corona-graph.js';
import {pointSymmetries,neighboringPairs} from '../../apps/3d-lattice-tiler/marking-learning.js';
const token=pair=>pair.map(placementKey).join('|');
function transformed(p,g){const mapped=g.map[p.oi];return {oi:mapped.oi,translation:add(g.transform(p.translation),mapped.shift)};}
function normalized(pair,g,swap){
 const rotated=pair.map(p=>transformed(p,g));if(swap)rotated.reverse();
 const origin=rotated[0].translation;
 return {pair:rotated.map(p=>({...p,translation:sub(p.translation,origin)})),origin};
}
export function pairOrbits(model){
 const transforms=pointSymmetries(model);
 // This additional condition makes global re-rooting an allowed translation,
 // rather than assuming all orientation-normalization offsets preserve L.
 if(transforms.some(g=>g.map.some(m=>!allowedTranslation(model,m.shift))))throw Error('Pair orbit normalization leaves the declared lattice');
 const pairs=[...neighboringPairs(model,transforms)],groups=new Map();
 for(let index=0;index<pairs.length;index++){
  const pair=pairs[index];let key=null;
  for(const g of transforms)for(const swap of [false,true]){const k=token(normalized(pair,g,swap).pair);if(key===null||k<key)key=k;}
  if(!groups.has(key))groups.set(key,{key,pair,members:[]});
  const group=groups.get(key);let transport=null;
  outer:for(let gi=0;gi<transforms.length;gi++)for(const swap of [false,true]){
   const n=normalized(group.pair,transforms[gi],swap);
   if(token(n.pair)===token(pair)){transport={gi,origin:n.origin,swap};break outer;}
  }
  if(!transport)throw Error('Pair orbit lacks an exact transport');
  group.members.push({index,pair,transport});
 }
 return {pairs,groups:[...groups.values()],transforms};
}
export function transportPatch(placements,member,transforms){
 const {gi,origin}=member.transport,g=transforms[gi];
 const mapped=placements.map(p=>{const q=transformed(p,g);return {...q,translation:sub(q.translation,origin)};});
 const seeds=new Set(member.pair.map(placementKey));
 return [...member.pair,...mapped.filter(p=>!seeds.has(placementKey(p)))];
}
