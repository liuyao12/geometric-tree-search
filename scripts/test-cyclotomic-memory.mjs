import assert from 'node:assert/strict';
import {blindPenroseProblem} from '../assets/penrose-blind-problem.js';
import {createObstructionSearch} from '../assets/cyclotomic-obstruction-search.js';
import {cycloAdd,latticeKey} from '../assets/cyclotomic-five.js';
const s=createObstructionSearch({problem:blindPenroseProblem(),learn:true,targetCount:12});while(!s.next().done){}
const a=s.snapshot(),positions=new Set(),values=new Set(),templates=new Map(a.learning.tables.map(t=>[t.type,t.rows]));
for(const t of a.tiles)for(const r of templates.get(t.type)||[]){const p=latticeKey(cycloAdd(t.origin,r.offset));positions.add(p);values.add(p+'@'+r.channel+':'+r.value);}
assert.deepEqual(a.memory.activeMarking,{points:positions.size,values:values.size});
assert.equal(a.learning.entries,a.learning.tables.reduce((n,t)=>n+t.rows.length,0));
assert.equal(a.learning.addresses,a.learning.tables.reduce((n,t)=>n+new Set(t.rows.map(r=>latticeKey(r.offset))).size,0));
assert.equal(a.memory.tPoints,new Set(a.tiles.flatMap(t=>t.vertices)).size);assert.equal(a.memory.tValues,a.memory.tPoints);assert(a.graph.retainedCandidates>=a.graph.candidates);
let result;globalThis.self={postMessage:s=>{result=s;}};await import('../apps/penrose-model-set/learning-worker.js');
for(const mode of ['known','plain']){self.onmessage({data:{type:'init',mode}});assert(!result.error,result.error);assert.equal(result.memory.activeMarking.values,0);if(mode==='known'){assert.equal(result.memory.bars.segments,5);assert.equal(result.memory.bars.familyValues,5);assert.equal(result.memory.bars.endpointReferences,10);}}
console.log('ok: template/active marking memory, t field, retained graph records, and continuous-bar accounting');
