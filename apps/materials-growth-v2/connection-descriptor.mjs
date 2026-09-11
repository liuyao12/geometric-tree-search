// Experimental compatibility hypothesis, not a physical potential or an exact
// isometry classifier. Pair-distance multisets can be homometric and cannot
// distinguish enantiomers. No rejection here proves geometric impossibility.
import {distance, sub, norm, cross, dot, add, scale} from './geometry.mjs';

export function connectionDescriptor(sites, crossChannels = true) {
  const buckets = new Map();
  for (let i = 0; i < sites.length; i++) for (let j = 0; j < i; j++) {
    const a = sites[i], b = sites[j];
    if (!crossChannels && ((a.role === 'A' && b.role === 'B') || (a.role === 'B' && b.role === 'A'))) continue;
    const key = JSON.stringify([a.role+':'+a.species,b.role+':'+b.species].sort());
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key).push(distance(a.position,b.position));
  }
  const keys = [...buckets.keys()].sort();
  return {key: JSON.stringify(keys.map(k=>[k,buckets.get(k).length])), values:keys.flatMap(k=>buckets.get(k).sort((a,b)=>a-b))};
}
export function descriptorDistance(a,b) {
  if(a.key !== b.key) return Infinity;
  return Math.max(0,...a.values.map((x,i)=>Math.abs(x-b.values[i])));
}
export function fitConnectionLibrary(examples, crossChannels=true) {
  const buckets = new Map();
  for(const example of examples){
    const d=connectionDescriptor(example.sites,crossChannels);
    if(!buckets.has(d.key)) buckets.set(d.key,[]);
    buckets.get(d.key).push(d);
  }
  return {crossChannels,buckets,size:examples.length};
}
export function connectionScore(library,sites) {
  const d=connectionDescriptor(sites,library.crossChannels);
  let best=Infinity;
  for(const ref of library.buckets.get(d.key)||[]) best=Math.min(best,descriptorDistance(d,ref));
  return best;
}
export function twistConnection(sites,angle) {
  const origin=sites[0].position, axis=scale(sub(sites[1].position,origin),1/distance(sites[0].position,sites[1].position));
  return sites.map(s=>{
    if(s.role!=='B') return {...s,position:[...s.position]};
    const v=sub(s.position,origin);
    const rotated=add(add(scale(v,Math.cos(angle)),scale(cross(axis,v),Math.sin(angle))),scale(axis,dot(axis,v)*(1-Math.cos(angle))));
    return {...s,position:add(origin,rotated)};
  });
}
// Two overlapping four-point motifs; two common anchors form a free hinge.
// Fixed-size nearest collections are a declared diagnostic, not motif discovery.
export function hingeExamples(atoms,{cell=null,margin=6,box=null}={}) {
  const result=[], seen=new Set();
  const delta=(a,b)=>b.map((v,k)=>{let d=v-a[k];return cell?d-cell*Math.round(d/cell):d;});
  for(let i=0;i<atoms.length;i++){
    const origin=atoms[i].position;
    if(box && origin.some(v=>Math.abs(v)>box/2-margin)) continue;
    const rows=atoms.map((a,j)=>({j,d:norm(delta(origin,a.position))})).filter(r=>r.j!==i).sort((a,b)=>a.d-b.d||a.j-b.j);
    const j=rows[0].j, pair=[i,j].sort((a,b)=>a-b).join(':');
    if(seen.has(pair))continue;seen.add(pair);
    const a=rows.filter(r=>r.j!==j).slice(0,2).map(r=>r.j);
    const b=atoms.map((p,k)=>({j:k,d:norm(delta(atoms[j].position,p.position))})).filter(r=>r.j!==i&&r.j!==j&&!a.includes(r.j)).sort((a,b)=>a.d-b.d||a.j-b.j).slice(0,2).map(r=>r.j);
    const ids=[i,j,...a,...b];
    const sites=ids.map((id,k)=>({id,species:atoms[id].species,role:['P','Q','A','A','B','B'][k],position:delta(origin,atoms[id].position)}));
    if(sites.some(s=>norm(s.position)>margin))continue;
    result.push({anchor:i,ids,origin:[...origin],sites});
  }
  return result;
}
