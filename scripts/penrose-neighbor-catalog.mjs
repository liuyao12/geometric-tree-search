import {mixedVariants,translateVariant,mixedGeometryConflict} from '../assets/penrose-mixed-growth.js';
import {tileStates} from '../assets/penrose-mixed-markings.js';
import {num,sub} from '../assets/penrose-polygon.js';
// Complete for the current finite orientation catalog and at least one shared
// vertex. Non-overlap and whole-edge geometry are checked before labeling.
export function neighborCatalog(progress=()=>{}) {
  const variants=mixedVariants(),result=[];
  for(const kind of [...new Set(variants.map(v=>v.kind))]) {
    const a=translateVariant(variants.find(v=>v.kind===kind),num(0));
    const labels=tileStates(a)[0].signatures,seen=new Set();let count=0;
    for(const v of variants)for(const p of a.exactPoints)for(const q of v.exactPoints){
      const b=translateVariant(v,sub(p,q));if(seen.has(b.id))continue;seen.add(b.id);
      if(mixedGeometryConflict(a,b))continue;
      const other=tileStates(b)[0].signatures,shared=[...labels.keys()].filter(e=>other.has(e));
      result.push({a,b,shared:shared.length,good:shared.every(e=>labels.get(e)===other.get(e))});count++;
    }
    progress(kind,count);
  }
  return result;
}
