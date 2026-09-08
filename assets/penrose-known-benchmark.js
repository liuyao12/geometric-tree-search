import {MIXED_TEMPLATES} from './penrose-mixed-templates.js?v=20260908-speed';
import {canonical} from './cyclotomic-five.js?v=20260908-speed';
import {num,add,sub,mul,conj} from './penrose-polygon.js?v=20260908-speed';
import {arrowStates} from './penrose-arrows.js?v=20260908-speed';
import {ammannStates,exactlyPerpendicular} from './penrose-ammann.js?v=20260908-speed';
import {mixedMarkingsCompatible,extendedBars} from './penrose-mixed-markings.js?v=20260908-speed';
import {box} from './penrose-polygon.js?v=20260908-speed';
// Benchmark-only adapter. It is never supplied to the blind learner.
export function knownPenroseBenchmark(problem,extent=2){
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
 const boxes=new WeakMap(),footprint=t=>{if(!boxes.has(t))boxes.set(t,box([...t.exactPoints,...extendedBars(marked(t),extent).flatMap(b=>[b.from,b.to])]));return boxes.get(t);};
 const direct=(a,b)=>mixedMarkingsCompatible(marked(a),marked(b),extent);
 return{decorate:marked,problem:{...problem,footprint},extraAllowed:problem.memoizePairs?problem.memoizePairs(direct,{footprint}):direct};
}
