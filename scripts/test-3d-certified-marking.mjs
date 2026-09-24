import assert from 'node:assert/strict';
import {compileCertifiedPairs,learnCertifiedMarking,reuseCertifiedMarking,certifiedSymmetries,pairOrbitKey,CERTIFIED_METHOD} from '../apps/3d-lattice-tiler/certified-marking.js';
import {neighboringPairs,pairCompatible} from '../apps/3d-lattice-tiler/marking-learning.js';
import {markingSystem,remember3DMarking} from '../apps/3d-lattice-tiler/marking-storage.js';
import {verifyCorona,add,sub,pointKey,allowedTranslation} from '../apps/3d-lattice-tiler/corona-graph.js';
import {GrowthGraph} from '../apps/3d-lattice-tiler/growth-search.js';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {runExperiment} from '../apps/3d-lattice-tiler/v2/experiment.js';
const collect=async stream=>{const events=[];for await(const e of stream)events.push(e);return events;};
const toy={capacity:3,allowReflections:false,orientations:[{type:0,index:0,cells:[2,1,2].map((weight,x)=>({pos:[x,0,0],weight})),vertices:[],faces:[]}]};
const pair=[{oi:0,translation:[0,0,0]},{oi:0,translation:[1,0,0]}];
const learned=(await collect(learnCertifiedMarking(toy,{pairNodes:0,timeMs:1000}))).at(-1);
assert(learned.marking.accepted);assert(learned.marking.redundant);assert.equal(learned.marking.counts.valid,0);assert(learned.marking.negativeBlocked>0);assert(!learned.marking.fallback);
assert(!pairCompatible(learned.marking.fields,pair));
assert(learned.marking.fields.flat().some(m=>m.value===0),'zero is an assigned value');
// Independent implication check for every mismatch, including non-neighbors:
// a rejected legal pose must have a freshly verified local obstruction.
for(let x=-6;x<=6;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++){
 const p=[pair[0],{oi:0,translation:[x,y,z]}];if(x===0&&y===0&&z===0)continue;
 if(!pairCompatible(learned.marking.fields,p))assert(verifyCorona(toy,p,p).deadPoints.length);
}
// Reflections and a real three-dimensional point group. A single certified
// Turtle orbit is compiled; all other orbits (including unresolved) must agree.
const turtle=prepareModel({tile:'a2_turtle_prism',radius:1,mirrors:true}),transforms=certifiedSymmetries(turtle),pairs=[...neighboringPairs(turtle,transforms)];
const bad=pairs.find(p=>verifyCorona(turtle,p,p).deadPoints.length);assert(bad);
const proof={pair:bad,status:'invalid',certificate:{kind:'dead_point',point:verifyCorona(turtle,bad,bad).deadPoints[0]}};
const compiled=compileCertifiedPairs(turtle,[proof]),badKey=pairOrbitKey(bad,transforms);
let preserved=0,blocked=0;
for(const p of pairs){const expected=pairOrbitKey(p,transforms)!==badKey;assert.equal(pairCompatible(compiled.fields,p),expected);if(expected)preserved++;else blocked++;}
assert(preserved>0&&blocked>0);
for(const [gi,g] of transforms.entries())for(const [oi,field] of compiled.fields.entries())for(const m of field){
 const expected={pos:sub(g.transform(m.pos),g.map[oi].shift),component:compiled.componentAction[gi][m.component],value:m.value};
 assert(compiled.fields[g.map[oi].oi].some(n=>JSON.stringify(n)===JSON.stringify(expected)));
}
assert.equal(compileCertifiedPairs(turtle,[proof],{maxComponents:0}).compiled.length,0,'budget cannot create a partial symmetry orbit');
// Exact graph updates and rollback under the new sparse channels, including
// independent enumeration instead of trusting cached candidate validity.
const marked={...turtle,orientations:turtle.orientations.map((o,i)=>({...o,marks:compiled.fields[i]}))},graph=new GrowthGraph(marked);
const digest=()=>JSON.stringify({totals:[...graph.totals].sort(),section:[...graph.section].sort(),selected:graph.descriptors()});
const before=digest(),undo=graph.apply(bad[0],{root:true});assert(!graph.candidate(bad[1].oi,bad[1].translation).valid);
for(const key of graph.active){const pos=key.split(',').map(Number),expected=new Set();for(const [oi,o] of marked.orientations.entries())for(const anchor of o.cells){const t=sub(pos,anchor.pos),id=`${oi}@${t}`;if(!allowedTranslation(marked,t)||graph.used.has(id))continue;if(!o.cells.every(c=>(graph.totals.get(pointKey(add(c.pos,t)))??0)+c.weight<=marked.capacity))continue;if(pairCompatible(compiled.fields,[bad[0],{oi,translation:t}]))expected.add(id);}assert.deepEqual(new Set([...graph.points.get(key).incident].filter(c=>c.valid).map(c=>c.id)),expected);}
graph.rollback(undo);assert.equal(digest(),before);assert(graph.candidate(bad[1].oi,bad[1].translation).valid);graph.audit();
// Saved negatives are re-proved, not trusted; field edits cannot introduce cuts.
const entry={domain:markingSystem(toy),marking:learned.marking};
const reused=(await collect(reuseCertifiedMarking(toy,entry))).at(-1);assert.deepEqual(reused.marking.fields,learned.marking.fields);
const tampered=structuredClone(entry);tampered.marking.proofs[0].certificate.point=[999,0,0];await assert.rejects(collect(reuseCertifiedMarking(toy,tampered)),/proof failed/);
const badFields=structuredClone(entry);badFields.marking.fields[0][0].value=99;await assert.rejects(collect(reuseCertifiedMarking(toy,badFields)),/modified/);
await assert.rejects(collect(reuseCertifiedMarking({...toy,capacity:4},entry)),/different system/);
// Partial catalogues and a zero preparation budget remain safe and can search.
const partial=(await collect(learnCertifiedMarking(toy,{maxPairs:1,timeMs:1000,pairNodes:0}))).at(-1);assert(partial.marking.accepted);assert(!partial.marking.catalogComplete);
const zero=(await collect(learnCertifiedMarking(toy,{timeMs:0}))).at(-1);assert(zero.marking.accepted);assert(zero.marking.fallback);assert(zero.model.orientations.every(o=>o.marks.length===0));
let saves=0;remember3DMarking(toy,zero.marking,{getItem:()=>null,setItem:()=>saves++});assert.equal(saves,0);
const nonacube=prepareModel({tile:'nonacube_cross',radius:1,mirrors:false});
const nc=(await collect(learnCertifiedMarking(nonacube,{pairNodes:0,timeMs:5000}))).at(-1);assert.equal(nc.marking.pairs,60);assert.equal(nc.marking.rawPairs,686);assert.equal(nc.marking.negativeBlocked,0);assert.equal(nc.marking.counts.unresolved,60);assert(nc.marking.accepted&&nc.marking.fallback);assert(nc.marking.evidence.every(r=>pairCompatible(nc.marking.fields,r.pair)));
for(const searchProtocol of ['seed-growth','fixed-window']){
 const es=await collect(runExperiment({tile:'cube',radius:1,mirrors:false,searchProtocol,mode:'gcts',markingMethod:CERTIFIED_METHOD,pairNodes:0,timeMs:5000,targetTiles:4,nodes:1000}));
 assert(!es.some(e=>e.type==='error'),es.at(-1)?.message);const r=es.at(-1);assert(r.marking.fallback);assert.equal(r.result,searchProtocol==='seed-growth'?'growth_checkpoint':'finite_exact');assert(r.stats.attempts>0);assert(r.stats.preparationMs<=r.stats.totalMs);
}
console.log(`PASS certified negative-only markings: no positives required; sparse component covariance; ${blocked} forbidden Turtle poses and ${preserved} preserved neighbors; graph/rollback; saved-proof tampering; partial/budget fallback; nonacube 686 pairs / 60 orbits; both search protocols.`);
