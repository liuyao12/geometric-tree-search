import {MIXED_TEMPLATES} from './penrose-mixed-templates.js?v=20260908-speed';
import {canonical} from './cyclotomic-five.js?v=20260908-speed';
import {num,add,sub,mul,conj} from './penrose-polygon.js?v=20260908-speed';
import {arrowStates} from './penrose-arrows.js?v=20260908-speed';
import {ammannStates,exactlyPerpendicular} from './penrose-ammann.js?v=20260908-speed';
import {orient} from './penrose-polygon.js?v=20260908-speed';
import {geometricPlacementAllowed} from './cyclotomic-tile-catalog.js?v=20260908-lines';
// A connected polygon meets an infinite line iff its vertices touch or
// straddle that line. Exact orientations include tangency and concave tiles.
export function infiniteLinesCompatible(a,b){
 for(const [source,target] of [[a,b],[b,a]])for(const line of source.bars){
  const signs=target.exactPoints.map(p=>orient(line.from,line.to,p));
  if(signs.every(s=>s>0)||signs.every(s=>s<0))continue;
  if(!target.bars.some(t=>t.family===line.family&&!orient(line.from,line.to,t.from)&&!orient(line.from,line.to,t.to)))return false;
 }
 return true;
}
// Benchmark-only adapter. It is never supplied to the blind learner.
export function knownPenroseBenchmark(problem){
 const cache=new WeakMap();
 function marked(t){if(!cache.has(t)){
  if(t.labels.some(l=>l.ports)){
   const original=MIXED_TEMPLATES.find(p=>p.kind===t.kind),g=t.sourceTransform;
   const transform=p=>add(sub(mul(g.factor,g.reflect?conj(p):p),g.offset),t.origin);
   const axes=Array.from({length:5},(_,i)=>canonical({coeff:Array.from({length:5},(_,j)=>+(i===j)),denominator:1}));
   const bars=original.bars.map(b=>{const from=transform(b.from),to=transform(b.to);return{from,to,family:axes.findIndex(a=>exactlyPerpendicular(sub(to,from),a))};});
   cache.set(t,{...t,bars});return cache.get(t);
  }
  const arrow=arrowStates(t).find(s=>[...s.signatures].every(([e,v])=>t.signatures.get(e)===v));
  if(!arrow)throw Error('Independent input arrows do not match the benchmark orientation');
  const state=ammannStates(t).find(s=>s.start===arrow.start);cache.set(t,{...t,bars:state.bars,arrowStart:arrow.start});
 }return cache.get(t);}
 // Every candidate may be affected by a distant infinite line. A common
 // bucket deliberately disables finite-distance pruning in the graph/cache.
 const footprint=()=>({x0:0,x1:0,y0:0,y1:0});
 const direct=(a,b)=>infiniteLinesCompatible(marked(a),marked(b));
 const pairAllowed=problem.memoizePairs?problem.memoizePairs(geometricPlacementAllowed):geometricPlacementAllowed;
 return{decorate:marked,problem:{...problem,pairAllowed,footprint},extraAllowed:problem.memoizePairs?problem.memoizePairs(direct,{footprint}):direct};
}
