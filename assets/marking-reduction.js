import {A2_TILE_LOOPS,tileOrientations,a2Transform,SparseA2Marking} from './a2-tiling-engine.js?v=20260915-three-sets';
const parity=p=>((p[0]>p[1])+(p[0]>p[2])+(p[1]>p[2]))%2?-1:1;
const pointKey=e=>`${e.tile}:${e.point}`;
export const activeMarkingSupport=model=>model?.reducedSupport??model?.support??[];

// All conflicts arise at an aligned pair of assigned point/channel values.
// Fix the first tile's orientation to identity by equivariance, enumerate every
// allowed relative orientation and alignment, and keep even mark-only contacts.
// Pairs already forbidden by t-capacity need no additional marking witness.
function conflictGraph(model) {
  const support=model.support,points=[...new Set(support.map(pointKey))],index=new Map(points.map((p,i)=>[p,i]));
  const relations=[],witnesses=[],witnessIndex=new Map();
  const orientations=model.tiles.flatMap(tile=>tileOrientations(tile,A2_TILE_LOOPS[tile])).filter(o=>model.allowReflections||parity(o.symmetry.permutation)>0);
  for(const tile of model.tiles){
    const root=orientations.find(o=>o.tile===tile&&o.index===0),left=support.filter(e=>e.tile===tile);
    for(const o of orientations){
      const sign=parity(o.symmetry.permutation),right=support.filter(e=>e.tile===o.tile).map(e=>({...e,original:e,point:a2Transform(e.point,o.symmetry),component:o.symmetry.permutation.indexOf(e.component),value:e.value*sign}));
      const pairs=new Map();
      for(const a of left)for(const b of right){
        if(a.component!==b.component||a.value===b.value)continue;
        const shift=a.point.map((v,i)=>v-b.point[i]),key=shift.join(',');
        let pair=pairs.get(key);if(!pair){pair={shift,witnesses:new Set()};pairs.set(key,pair);}
        const x=index.get(pointKey(a)),y=index.get(pointKey(b.original)),token=x<=y?`${x}:${y}`:`${y}:${x}`;
        let w=witnessIndex.get(token);if(w===undefined){w=witnesses.length;witnessIndex.set(token,w);witnesses.push({points:[...new Set([x,y])],relations:[]});}
        pair.witnesses.add(w);
      }
      for(const pair of pairs.values()){
        if([...o.occupancy.values()].some(e=>e.weight+(root.occupancy.get(e.point.map((v,i)=>v+pair.shift[i]).join(','))?.weight||0)>12))continue;
        const r=relations.length;relations.push({key:`${tile}>${o.tile}:${o.index}:${pair.shift}`,witnesses:[...pair.witnesses]});
        for(const w of pair.witnesses)witnesses[w].relations.push(r);
      }
    }
  }
  return {points,relations,witnesses};
}

export function reduceMarking(model) {
  const {points,relations,witnesses}=conflictGraph(model),incident=points.map(()=>[]);
  witnesses.forEach((w,i)=>w.points.forEach(p=>incident[p].push(i)));
  const kept=points.map(()=>true),live=witnesses.map(()=>true),counts=relations.map(r=>r.witnesses.length);
  // Whole-point deletion removes all three channels, including assigned zeros.
  const order=points.map((_,i)=>i).sort((a,b)=>incident[a].reduce((n,w)=>n+witnesses[w].relations.length,0)-incident[b].reduce((n,w)=>n+witnesses[w].relations.length,0)||a-b);
  for(const p of order){
    const losses=new Map(),affected=incident[p].filter(w=>live[w]);
    for(const w of affected)for(const r of witnesses[w].relations)losses.set(r,(losses.get(r)||0)+1);
    if([...losses].some(([r,n])=>n>=counts[r]))continue;
    kept[p]=false;for(const w of affected)live[w]=false;for(const [r,n] of losses)counts[r]-=n;
  }
  const keep=new Set(points.filter((_,i)=>kept[i])),reducedSupport=model.support.filter(e=>keep.has(pointKey(e))).map(e=>({...e,point:[...e.point]}));
  return {...model,reducedSupport,reduction:{method:'all-legal-pair-conflicts-v1',originalPoints:points.length,points:keep.size,originalValues:model.support.length,values:reducedSupport.length,pairConflicts:relations.length,scope:'Same marking compatibility for every t-legal pair, including mark-only overlaps; no claim of equivalence to known markings.'}};
}

export function validateMarkingReduction(model) {
  if(model.reducedSupport===undefined)return;
  if(!Array.isArray(model.reducedSupport))throw new Error('Invalid reduced marking support');
  const full=new Map(model.support.map(e=>[`${pointKey(e)}|${e.component}`,e.value])),kept=new Set();
  for(const e of model.reducedSupport){if(!Array.isArray(e.point)||e.point.length!==3||!e.point.every(Number.isSafeInteger)||![0,1,2].includes(e.component)||!Number.isSafeInteger(e.value))throw new Error('Invalid reduced marking entry');const key=`${pointKey(e)}|${e.component}`;if(kept.has(key)||!full.has(key)||full.get(key)!==e.value)throw new Error('Invalid reduced marking entry');kept.add(key);}
  const reducedPoints=new Set(model.reducedSupport.map(pointKey));
  if(model.support.some(e=>reducedPoints.has(pointKey(e))&&!kept.has(`${pointKey(e)}|${e.component}`)))throw new Error('Reduction must retain whole points');
  const {points,relations,witnesses}=conflictGraph(model),live=points.map(p=>reducedPoints.has(p));
  if(relations.some(r=>!r.witnesses.some(w=>witnesses[w].points.every(p=>live[p]))))throw new Error('Reduction lost a marking conflict');
}


// Retain the original preference among legal candidates. The reduced entries
// drive compatibility and frontier dependencies; dense entries only score ties.
export class CompactA2Marking extends SparseA2Marking {
  constructor(model) { super(activeMarkingSupport(model)); this.ranking=new SparseA2Marking(model.support); }
  reset(context=[]) { this.contacts=new Map(); this.ranking.reset(); for(const p of context)this.push(p); }
  push(placement) { super.push(placement); this.ranking.push(placement); }
  pop(placement) { super.pop(placement); this.ranking.pop(placement); }
  score(candidate) { return this.ranking.score(candidate); }
}
