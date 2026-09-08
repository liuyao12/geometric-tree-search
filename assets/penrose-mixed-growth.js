import {canonical,embedding,latticeKey} from './cyclotomic-five.js';
import {MIXED_TEMPLATES} from './penrose-mixed-templates.js';
import {ammannStates,exactlyPerpendicular} from './penrose-ammann.js?v=20260907-extent';
import {validateExtent} from './penrose-extensions.js?v=20260907-extent';
import {num,add,sub,mul,conj,areaSign,overlap,onSegment,same,box,separated} from './penrose-polygon.js';
import {tileStates,edgeKey,mixedMarkingsCompatible} from './penrose-mixed-markings.js?v=20260907-frontier';
import { createPenrosePointSearch } from './penrose-point-search.js?v=20260907-contacts';
export const TILE_KINDS=['thick','thin','kite','dart','p5','p3','p2','diamond','boat','star'];
const axes=Array.from({length:5},(_,i)=>canonical({coeff:Array.from({length:5},(_,j)=>+(i===j)),denominator:1}));
const hash=(s,seed)=>{let h=(2166136261^seed)>>>0;for(const c of s)h=Math.imul(h^c.charCodeAt(0),16777619)>>>0;return h;};
let variants;
export function mixedVariants(){
  if(variants)return variants;
  const unique=new Map();
  for(const template of MIXED_TEMPLATES)for(const reflect of[false,true])for(const axis of axes)for(const sign of[1,-1]){
    const factor=mul(axis,num(sign)),transform=p=>mul(factor,reflect?conj(p):p);
    let exactPoints=template.exactPoints.map(transform),weights=template.weights.slice();
    if(areaSign(exactPoints)<0){exactPoints.reverse();weights.reverse();}
    const bars=template.bars.map(b=>{const from=transform(b.from),to=transform(b.to);return{from,to,family:axes.findIndex(a=>exactlyPerpendicular(sub(to,from),a))};});
    const id=template.kind+':'+exactPoints.map(latticeKey).sort().join('|')+'@'+bars.map(b=>[latticeKey(b.from),latticeKey(b.to)].sort().join('>')).sort().join('|');
    const variant={kind:template.kind,presentation:template.presentation,exactPoints,weights,bars,variantId:id};
    if(template.presentation==='P3'){
      const signature=bs=>bs.map(b=>[latticeKey(b.from),latticeKey(b.to)].sort().join('>')).sort().join('|');
      variant.arrowStart=ammannStates(variant).find(s=>signature(s.bars)===signature(bars))?.start;
      if(variant.arrowStart===undefined)throw Error('Rhomb decoration has no arrow orientation');
    }
    unique.set(id,variant);
  }
  variants=[...unique.values()];return variants;
}
export function translateVariant(v,delta){
  const exactPoints=v.exactPoints.map(p=>add(p,delta)),vertices=exactPoints.map(latticeKey);
  const bars=v.bars.map(b=>({...b,from:add(b.from,delta),to:add(b.to,delta)}));
  const id=v.kind+':'+vertices.slice().sort().join('|')+'@'+bars.map(b=>[latticeKey(b.from),latticeKey(b.to)].sort().join('>')).sort().join('|');
  return {kind:v.kind,presentation:v.presentation,exactPoints,vertices,weights:v.weights,bars,id,arrowStart:v.arrowStart};
}
export function mixedGeometryConflict(a,b){
  if(separated(box(a.exactPoints),box(b.exactPoints)))return false;
  if(overlap(a.exactPoints,b.exactPoints))return true;
  // Whole-edge placement excludes T-junctions and partial edge contacts.
  for(const[p,q]of[[a,b],[b,a]])for(const v of p.exactPoints)for(let k=0;k<q.exactPoints.length;k++){
    const x=q.exactPoints[k],y=q.exactPoints[(k+1)%q.exactPoints.length];
    if(!same(v,x)&&!same(v,y)&&onSegment(v,x,y))return true;
  }
  return false;
}
export function createMixedGrowth(options={}) { return createPenrosePointSearch(options); }
