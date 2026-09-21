import assert from 'node:assert/strict';
import {CoronaGraph,checkCorona,verifyCorona,placementKey,add,pointKey} from '../apps/3d-lattice-tiler/corona-graph.js';
import {learnMarking,pairCompatible,LearnedSection} from '../apps/3d-lattice-tiler/marking-learning.js';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {search,verify,PointGraph} from '../apps/3d-lattice-tiler/v2/search.js';
import {createTilingStream,tileSpecs} from '../apps/3d-lattice-tiler/engine.js';
import {remember3DMarking,STORAGE_KEY} from '../apps/3d-lattice-tiler/marking-storage.js';
const toy=weights=>({capacity:3,orientations:[{type:0,index:0,cells:weights.map((weight,x)=>({pos:[x,0,0],weight})),vertices:[],faces:[]}],allowReflections:false});
const pair=[{oi:0,translation:[0,0,0]},{oi:0,translation:[1,0,0]}];
const collect=async stream=>{let last;for await(const e of stream)last=e;return last;};
// Complete forward/reverse incidence against a fresh independent enumerator.
function audit(graph){
 graph.audit();
 for(const k of graph.active){const point=k.split(',').map(Number),expected=new Set();for(let oi=0;oi<graph.model.orientations.length;oi++)for(const a of graph.model.orientations[oi].cells){const translation=point.map((v,i)=>v-a.pos[i]),id=placementKey({oi,translation});if(graph.used.has(id))continue;if(graph.model.orientations[oi].cells.every(c=>(graph.totals.get(pointKey(add(c.pos,translation)))??0)+c.weight<=graph.model.capacity))expected.add(id);}assert.deepEqual(new Set([...graph.point(k).incident].filter(c=>c.valid).map(c=>c.id)),expected);}
}
const state=g=>JSON.stringify({totals:[...g.totals].sort(),generations:[...g.generations].map(([k,v])=>[k,[...v].sort()]).sort(),active:[...g.active].sort(),selected:g.descriptors()});
const g=new CoronaGraph(toy([1,2]));for(const p of pair)g.apply(p,{root:true});audit(g);const before=state(g);
for(const p of [...g.active])for(const c of [...g.point(p).incident].filter(c=>c.valid)){
 const undo=g.apply(c);audit(g);const next=g.schedule();if(next.point){const child=[...next.point.incident].find(c=>c.valid);if(child){const u=g.apply(child);audit(g);g.rollback(u);audit(g);}}g.rollback(undo);assert.equal(state(g),before);audit(g);
}
const positive=await collect(checkCorona(toy([1,2]),pair,{audit:true}));assert.equal(positive.status,'valid');assert.ok(verifyCorona(toy([1,2]),pair,positive.placements).complete);
const negative=await collect(checkCorona(toy([2,1,2]),pair,{audit:true}));assert.equal(negative.status,'invalid');
assert.equal((await collect(checkCorona(toy([1,2]),pair,{nodes:0}))).status,'unresolved');
assert.equal((await collect(checkCorona(toy([1,2]),pair,{candidateLimit:1}))).status,'unresolved');
// A completed pair core can still expose a dead outer frontier.
const badModel={capacity:3,orientations:[{type:0,index:0,cells:[{pos:[0,0,0],weight:3}],vertices:[],faces:[]},{type:1,index:0,cells:[{pos:[0,0,0],weight:1}],vertices:[],faces:[]}]};
const fixed=[{oi:0,translation:[0,0,0]},{oi:0,translation:[1,0,0]}];const frontier=verifyCorona(badModel,fixed,[...fixed,{oi:1,translation:[2,0,0]}]);assert.ok(frontier.coreComplete);assert.equal(frontier.frontierViable,false);assert.equal(frontier.complete,false);
// Independent vector components: * is absent, zero is assigned.
const decorated={capacity:1,required:[{pos:[0,0,0]},{pos:[1,0,0]}],orientations:[{cells:[{pos:[0,0,0],weight:1}],marks:[{pos:[4,0,0],value:[null,0]}]},{cells:[{pos:[0,0,0],weight:1}],marks:[{pos:[3,0,0],value:[1,1]}]}]};
const dg=new PointGraph(decorated),a=dg.candidates.find(c=>c.oi===0&&c.translation[0]===0),b=dg.candidates.find(c=>c.oi===1&&c.translation[0]===1),undo=dg.apply(a);assert.equal(b.valid,false);assert.ok(dg.markingCuts);dg.rollback(undo);assert.ok(b.valid);dg.verifyDomains();
for(const [tile,pairs,valid,invalid,blocked] of [['cube',26,26,0,0],['a2_turtle_prism',247,41,206,176],['a2_hat_prism',227,41,186,166]]){
 const model=prepareModel({tile,radius:1,mirrors:true});let previous=0,last;
 for await(const e of learnMarking(model,{timeMs:30000,audit:tile==='cube'})){
  if(e.phase==='update'){assert.equal(e.pairs,++previous);assert.equal(e.snapshot.counts.valid,e.snapshot.positivePassed);assert.equal(e.snapshot.saved,undefined);}
  last=e;
 }
 const marking=last.marking;assert.ok(marking.accepted);assert.ok(marking.complete);assert.equal(marking.pairs,pairs);assert.deepEqual(marking.counts,{valid,invalid,unresolved:0});assert.equal(marking.negativeBlocked,blocked);
 for(const row of marking.evidence){if(row.status==='valid'){assert.ok(verifyCorona(model,row.pair,row.placements).complete);assert.ok(pairCompatible(marking.fields,row.pair));}}
 assert.equal(marking.evidence.filter(row=>row.status==='invalid'&&!pairCompatible(marking.fields,row.pair)).length,blocked);
 const grown=await collect(search(last.model,{mode:'gcts',learnedRestriction:true,timeMs:5000,nodes:10000}));assert.equal(grown.result,'finite_exact');assert.ok(verify(last.model,grown.placements).ok);assert.ok(verify(model,grown.placements).ok);
 const section=new LearnedSection(model,marking),spec=marking.evidence[0].pair[0],o=model.orientations[spec.oi],move={type:o.type,index:o.index,translation:spec.translation};section.add(move);section.add(move);section.remove(move);assert.ok(section.compatible(move));section.remove(move);assert.equal(section.section.size,0);
 console.log(`${tile}: ${pairs} labels, all ${valid} positives pass, ${blocked}/${invalid} negatives blocked, marked finite window verified.`);
}
const short=await collect(learnMarking(prepareModel({tile:'cube',radius:1}),{maxPairs:1,timeMs:10000}));assert.equal(short.marking.complete,false);assert.equal(short.marking.accepted,false);assert.equal(short.model,null);
const unknown=await collect(learnMarking(prepareModel({tile:'cube',radius:1}),{pairNodes:0,timeMs:10000}));assert.equal(unknown.marking.accepted,false);assert.ok(unknown.marking.counts.unresolved);assert.equal(unknown.model,null);
// Legacy v1 integration, plus acceptance/storage boundary.
let learned,final;for await(const e of createTilingStream({mode_key:'cube',tiling_strategy:'learning_free_range',gcts_failure_marking:true,complete_lattice_point_branching:true,criterion:'count',target_val:8,time_limit_ms:5000,node_limit:1000},tileSpecs)){if(e.type==='marking-learned')learned=e.marking;if(e.type==='finished')final=e;}
assert.ok(learned.accepted);assert.ok(final.success);assert.equal(final.search_stats.marking_kind,'learned_pair_corona_section');
const store=new Map(),storage={getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,v)},m=prepareModel({tile:'cube',radius:1});remember3DMarking(m,{accepted:false},storage);assert.equal(store.size,0);const saved=remember3DMarking(m,learned,storage);assert.ok(saved.saved.persisted);assert.equal(JSON.parse(store.get(STORAGE_KEY)).length,1);remember3DMarking(m,saved,storage);assert.equal(JSON.parse(store.get(STORAGE_KEY)).length,1);
console.log('PASS complete dynamic domains, generation rollback, independent frontier check, unknown budgets, component wildcards, both engines and browser-only save gate.');
