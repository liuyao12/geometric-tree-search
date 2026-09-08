import assert from 'node:assert/strict';
import {selectedPenroseProblem,TILE_PRESETS} from '../assets/penrose-selection-problem.js';
import {createObstructionSearch} from '../assets/cyclotomic-obstruction-search.js';
import {knownPenroseBenchmark} from '../assets/penrose-known-benchmark.js';
import {tileStates} from '../assets/penrose-mixed-markings.js';
import {num,mul,conj} from '../assets/penrose-polygon.js';
import {latticeKey} from '../assets/cyclotomic-five.js';
const barSignature=bars=>bars.map(b=>[latticeKey(b.from),latticeKey(b.to)].sort().join('>')).sort().join('|');
for(const [name,kinds] of Object.entries({...TILE_PRESETS,custom:['thick','kite'],single:['p5']})){
 const problem=selectedPenroseProblem(kinds),benchmark=knownPenroseBenchmark(problem);
 for(const t of problem.catalog){const a=problem.resolve(t.type,num(0));assert(kinds.includes(a.kind));
  for(const g of problem.actions){const target=problem.rigid(a,g),act=p=>mul(g.factor,g.reflect?conj(p):p);assert.equal(barSignature(benchmark.decorate(target).bars),barSignature(benchmark.decorate(a).bars.map(b=>({from:act(b.from),to:act(b.to)}))),'quotienting must preserve known decorations');}
  const marked=benchmark.decorate(a);assert(marked.bars.every(b=>b.family>=0));
  if(a.labels.some(l=>l.ports))for(const b of problem.movesAt(a.exactPoints[0])){
   // Check port equality against the independently retained continuous-bar
   // boundary extractor; include both accepted and rejected contacts.
   const sa=tileStates(marked)[0].signatures,sb=tileStates(benchmark.decorate(b))[0].signatures;
   for(const [edge,value] of a.signatures)if(b.signatures.has(edge))assert.equal(value===b.signatures.get(edge),sa.get(edge)===sb.get(edge));
  }
 }
 for(const mode of ['plain','learned','known']){const search=createObstructionSearch({...(mode==='known'?benchmark:{problem}),learn:mode==='learned',targetCount:8,nodeLimit:TILE_PRESETS[name]&&name!=='all'?250:20,seed:1});while(!search.next().done){}const s=search.snapshot();assert(s.tiles.every(t=>kinds.includes(t.kind)));assert(['target reached','budget reached','frontier exhausted'].includes(s.status));if(name==='P2'||name==='P1')assert.equal(s.status,'target reached');console.log(name,mode,s.status,s.tiles.length,s.learning?.rules||0);}
}
assert.throws(()=>selectedPenroseProblem([]),/Choose/);assert.throws(()=>selectedPenroseProblem(['bad']),/Choose/);
console.log('ok: all presets/custom subsets, exact boundary-rule agreement, rigid closure, and all three search lanes');
