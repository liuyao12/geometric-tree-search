import {arrowStates} from './penrose-arrows.js';
import {ammannStates} from './penrose-ammann.js';
import {mixedMarkingsCompatible,extendedBars} from './penrose-mixed-markings.js';
import {box} from './penrose-polygon.js';
// Benchmark-only adapter. It is never supplied to the blind learner.
export function knownPenroseBenchmark(problem,extent=2){
 const cache=new WeakMap();
 function marked(t){if(!cache.has(t)){
  const arrow=arrowStates(t).find(s=>[...s.signatures].every(([e,v])=>t.signatures.get(e)===v));
  if(!arrow)throw Error('Independent input arrows do not match the benchmark orientation');
  const state=ammannStates(t).find(s=>s.start===arrow.start);cache.set(t,{...t,bars:state.bars,arrowStart:arrow.start});
 }return cache.get(t);}
 return{decorate:marked,problem:{...problem,footprint:t=>box([...t.exactPoints,...extendedBars(marked(t),extent).flatMap(b=>[b.from,b.to])])},extraAllowed:(a,b)=>mixedMarkingsCompatible(marked(a),marked(b),extent)};
}
