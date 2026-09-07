import {latticeKey} from './cyclotomic-five.js';
import {ammannStates} from './penrose-ammann.js?v=20260907-extent';
import {extendBar,markingValue} from './penrose-extensions.js?v=20260907-extent';
import {pointInPolygon,onSegment,segmentCuts,lerp,num,add,mul,box,separated} from './penrose-polygon.js';
export const edgeKey=(a,b)=>[latticeKey(a),latticeKey(b)].sort().join('|');
const states=new WeakMap(),extensions=new WeakMap();
export function tileStates(tile){
  if(!tile.bars)return ammannStates(tile);
  if(!states.has(tile)){
    const signatures=new Map(tile.exactPoints.map((a,i)=>[edgeKey(a,tile.exactPoints[(i+1)%tile.exactPoints.length]),[]]));
    const bars=tile.bars.map((b,stripe)=>({...b,stripe,tileId:tile.id,ends:[{point:b.from},{point:b.to}]}));
    for(const b of bars)for(const p of[b.from,b.to])tile.exactPoints.forEach((a,i)=>{const q=tile.exactPoints[(i+1)%tile.exactPoints.length];if(onSegment(p,a,q))signatures.get(edgeKey(a,q)).push(`${latticeKey(p)}:${b.family}`);});
    states.set(tile,[{start:tile.arrowStart ?? 0,bars,signatures:new Map([...signatures].map(([k,v])=>[k,[...new Set(v)].sort().join(';')]))}]);
  }
  return states.get(tile);
}
export function extendedBars(tile,extent){let cache=extensions.get(tile);if(!cache){cache=new Map();extensions.set(tile,cache);}if(!cache.has(extent))cache.set(extent,tileStates(tile)[0].bars.map(b=>({...b,...extendBar(b,extent)})));return cache.get(extent);}
export function tileMarkingValue(tile,state,point,extent){
  if(!tile.bars)return markingValue(tile,state,point,extent);
  const inside=pointInPolygon(point,tile.exactPoints),bars=extendedBars(tile,extent),value=Array(5).fill(inside?0:null);
  for(const bar of bars)if(onSegment(point,bar.from,bar.to))value[bar.family]=1;
  return value.some(v=>v!==null)?value:null;
}
// Compare the whole support, including isolated boundary contacts and every
// interval through a concave tile. The displayed sample density is irrelevant.
export function mixedMarkingsCompatible(a,b,extent){
  for(const[source,target]of[[a,b],[b,a]]){
    const targetBars=extendedBars(target,extent);
    for(const bar of extendedBars(source,extent)){
      if(separated(box([bar.from,bar.to]),box(target.exactPoints)))continue;
      const matches=targetBars.filter(t=>t.family===bar.family);
      const covered=p=>matches.some(t=>onSegment(p,t.from,t.to));
      const cuts=segmentCuts(bar.from,bar.to,target.exactPoints),points=cuts.map(t=>lerp(bar.from,bar.to,t));
      for(const p of points)if(pointInPolygon(p,target.exactPoints)&&!covered(p))return false;
      for(let i=0;i<points.length-1;i++){
        const mid=lerp(bar.from,bar.to,mul(add(cuts[i],cuts[i+1]),num(1,2)));
        if(pointInPolygon(mid,target.exactPoints)&&!matches.some(t=>onSegment(points[i],t.from,t.to)&&onSegment(points[i+1],t.from,t.to)))return false;
      }
    }
  }
  return true;
}
