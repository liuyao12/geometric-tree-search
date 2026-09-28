import assert from 'node:assert/strict';
import {createFrontierGraph} from '../assets/tiling-frontier-graph.js';
const A={id:'A',vertices:['p','q']},B={id:'B',vertices:['q']},C={id:'C',vertices:['r']};
let blocked=new Set();
const graph=createFrontierGraph({enumerate:p=>({p:[A],q:[A,B],r:[C]})[p.key],legal:t=>!blocked.has(t.id),compatibleWithAddition:t=>!blocked.has(t.id),footprint:()=>({x0:0,x1:1,y0:0,y1:1})});
const point=(key,depth=0)=>({key,total:1,depth});
graph.build([point('p',10),point('q'),point('r')]);
assert.equal(graph.summary().candidates,3);assert.equal(graph.summary().incidences,4);
const before=graph.inspect();assert.equal(graph.choose().forced,true);
blocked=new Set(['A','C']);const delta=graph.push(A,[point('q'),point('r')]);
assert.equal(graph.choose().dead,true,'dead point wins over a forced point anywhere else');
blocked=new Set();graph.pop(delta);assert.deepEqual(graph.inspect(),before);
assert.equal(graph.summary().fullBuilds,1);assert.equal(graph.summary().rollbacks,1);
console.log('ok: shared candidate identities, global dead/forced priority and exact graph rollback');

const saved=graph.inspect();const refinement=graph.refine(t=>t.id!=="A");
assert(graph.choose().dead);assert(graph.inspect().filter(p=>p.key==="p"||p.key==="q").every(p=>!p.candidates.includes("A")));
graph.pop(refinement);assert.deepEqual(graph.inspect(),saved,"learned-domain refinement must trail every shared incidence");

// Earlier generation wins over a smaller non-singleton degree only in the
// reference mode. Preserve the historical mode for old benchmark callers.
for(const generationFirst of [false,true]){
 const options={early:[0,1,2].map(i=>({id:'e'+i,vertices:['early']})),late:[0,1].map(i=>({id:'l'+i,vertices:['late']}))};
 const g=createFrontierGraph({generationFirst,enumerate:p=>options[p.key],legal:()=>true,compatibleWithAddition:()=>true,footprint:()=>({x0:0,x1:0,y0:0,y1:0})});g.build([point('early',0),point('late',5)]);
 assert.equal(g.choose().point.key,generationFirst?'early':'late');
 const force=g.refine(t=>t.id!=='l1');assert.equal(g.choose().point.key,'late');assert(g.choose().forced);
 const kill=g.refine(t=>!t.id.startsWith('e'));assert(g.choose().dead);g.pop(kill);g.pop(force);
 assert.equal(g.choose().point.key,generationFirst?'early':'late');
}
console.log('ok: explicit generation-first scheduling preserves global dead/forced priority and historical default');
